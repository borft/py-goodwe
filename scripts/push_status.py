import json
import configparser
import datetime
import urllib
import requests
import math

from lib.db import db
from lib.pvoutput import pvoutput

## read config / ini file
config = configparser.ConfigParser()
config.read('config.ini')

cur = db(config).get_cursor()

query = """
WITH
    -- data range we generate data for generally
    -- this would be from now() - %s until now()
    data_range AS (
        SELECT 
            NOW() - INTERVAL '4h'   AS d_start,
            NOW()                   AS d_end
    ),
    -- range per date, 1 row per day
    data_range_days AS (
        SELECT date_trunc('day', dd):: date - INTERVAL '1 day' as date
        FROM generate_series( 
        (SELECT d_start::date FROM data_range), (SELECT d_end::date FROM data_range),'1 day'::interval) dd
        
    ),
    -- create mapping from 5 minute intervals to sems data
    -- make sure to have only one row per selected interval
    sems_sample_mapping AS (
        SELECT
            MIN(p.sample) as sample,
            p.rounded_sample
        FROM
            (SELECT 
                s.sample,
                timestamp without time zone 'epoch' +
                    round(extract(epoch from sample) /300)
                    * INTERVAL '300 second' as rounded_sample
            FROM sems s
            WHERE sample BETWEEN 
                (SELECT d_start FROM data_range) AND (SELECT d_end FROM data_range)
        ) as p
        GROUP BY p.rounded_sample
    ),
    -- mapping table with 5 minute intervals for electricity
    e_sample_mapping AS (
        SELECT 
            e.sample AS sample,
            timestamp without time zone 'epoch' +
                floor(extract(epoch from e.sample) /300)
                * INTERVAL '300 second' as rounded_sample
        FROM electricity e 
        WHERE 
            e.sample BETWEEN             
                (SELECT d_start FROM data_range) AND (SELECT d_end FROM data_range)
            AND CAST(EXTRACT(minute from sample) AS INT) % 5 = 0
        ORDER BY sample desc
    ),
    -- more exact match of timestamps between e and sems
    e_sample_mapping_combined AS (
        SELECT
            coalesce(e.sample, esm.sample) as sample,
            esm.rounded_sample AS rounded_sample
        FROM e_sample_mapping esm
        LEFT JOIN sems_sample_mapping ssm ON ssm.rounded_sample=esm.rounded_sample
        LEFT JOIN electricity e ON (
            DATE(e.sample) = DATE(ssm.sample)
            AND EXTRACT(hour FROM e.sample) = EXTRACT(hour from ssm.sample)
            AND extract(minute FROM e.sample) = EXTRACT(minute FROM ssm.sample))
    ),
    -- max totals of the previous day (should be 23:59)
    e_baseline AS (
        SELECT
            MAX(e.kwh_in_1)  AS kwh_in_1,
            MAX(e.kwh_in_2)  AS kwh_in_2,
            MAX(e.kwh_out_1) AS kwh_out_1,
            MAX(e.kwh_out_2) AS kwh_out_2,
            DATE(MAX(e.sample) + INTERVAL '1 day') AS date
        FROM electricity e
        WHERE 
            date(e.sample) IN (SELECT * FROM data_range_days)
        GROUP BY DATE(e.sample)
            
    ),
    sems_yield_today AS (
        SELECT
            MAX(s.yield_today) AS yield_today,
            MAX(s.sample) AS sample,
            DATE(s.sample) AS date
        FROM sems s
        WHERE
            date(s.sample) BETWEEN
                (SELECT DATE(d_start) FROM data_range) AND (SELECT d_end FROM data_range)
        GROUP BY DATE(s.sample)
    )

    SELECT 
        esm.rounded_sample AS sample,
        DATE(e.sample) AS date,
        CONCAT(
            lpad(cast(extract(hour from esm.rounded_sample) as varchar),2,'0'), 
            ':', 
            lpad(cast(extract(minute from esm.rounded_sample) as varchar),2,'0')) as time,
        
        e.power_in * 1000 AS power_in,
        e.power_out * 1000 AS power_out,
        (e.kwh_in_1 - eb.kwh_in_1) * 1000 as kwh_in_1,
        (e.kwh_in_2 - eb.kwh_in_2) * 1000 as kwh_in_2,
        (e.kwh_out_1 - eb.kwh_out_1) * 1000 as kwh_out_1,
        (e.kwh_out_2 - eb.kwh_out_2) * 1000 as kwh_out_2,

        coalesce(s.yield_today, 
            CASE WHEN syt.sample < e.sample THEN syt.yield_today ELSE 0 END) * 1000 AS yield_today,
        s.power_ac AS power_ac,
        s.power_dc_1,
        s.power_dc_2,
        s.current_dc_1,
        s.current_dc_2,
        s.voltage_dc_1,
        s.voltage_dc_2,
        (s.voltage_ac_1 + s.voltage_ac_2 + s.voltage_ac_3)/3 as voltage_ac,
        s.temperature,
        s.sample AS sems_sample

    FROM e_sample_mapping_combined esm
    INNER JOIN electricity e ON e.sample = esm.sample
    INNER JOIN e_baseline eb ON eb.date = DATE(e.sample)
    LEFT JOIN sems_sample_mapping ssm ON ssm.rounded_sample = esm.rounded_sample
    LEFT JOIN sems s on s.sample = ssm.sample
    LEFT JOIN sems_yield_today syt ON syt.date = DATE(e.sample) 
    ORDER BY sample ASC
"""

cur.execute(query)
rows = cur.fetchall()

data = []
for row in rows:
    if row['power_ac']:
        power_ac = row['power_ac']
    else:
        power_ac = 0
    if row['power_in']:
        power_in = row['power_in']
    else:
        power_in = 0
    if row['power_out']:
        power_out = row['power_out']
    else:
        power_out = 0
    energyConsumption = row['kwh_in_1'] + row['kwh_in_2'] - row['kwh_out_1'] - row['kwh_out_2'] + int(row['yield_today'])
    powerConsumption = power_ac + power_in - power_out
    data.append(
        ','.join(
            [str(e) for e in[
                row['date'].strftime('%Y%m%d'),
                row['time'],
                row['yield_today'],
                row['power_ac'],
                energyConsumption,
                powerConsumption,
                row['temperature'],
                row['voltage_ac'],
                row['power_dc_1'], row['power_dc_2'],
                row['current_dc_1'], row['current_dc_2'],
                row['voltage_dc_1'], row['voltage_dc_2']]
            ])
        )

print(f'got {len(data)} rows')


pvoutput = pvoutput(config['pvoutput']['api-key'], config['pvoutput']['site-id'])
responses = pvoutput.sendDataStatus(data=data)



for response in responses:
    if response:
        print(f'got response: {response.read().decode("utf-8")}')
    else:
        print('request failed')

