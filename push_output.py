from sensor import SemsSensor
import json
import configparser
import datetime
import urllib
import math

import db
import pvoutput

## read config / ini file
config = configparser.ConfigParser()
config.read('db.ini')

cur = db.db(config).get_cursor()

query = """

WITH
    data_range AS (
        SELECT
            NOW() - INTERVAL '1 day'    AS d_start,
            DATE(NOW())    AS d_end
    ),

    baseline AS (
        SELECT
            DATE(e.sample) + INTERVAL '1 day' AS date,
            MAX(kwh_in_1) + MAX(kwh_in_2) AS kwh_in,
            MAX(kwh_out_1) + MAX(kwh_out_2) AS kwh_out
        FROM electricity e
        WHERE DATE(e.sample) BETWEEN
            (SELECT d_start::date - INTERVAL '1 day' FROM data_range) AND (SELECT d_end::date - INTERVAL '1 day' FROM data_range)
        GROUP BY DATE(sample)
        ORDER BY DATE(sample)
    )

  SELECT
        TO_CHAR(DATE(e.sample), 'YYYYMMDD') AS d,
        1000*MAX(s.yield_today) AS g,
        1000* (MAX(e.kwh_out_1) + MAX(e.kwh_out_2) - MAX(b.kwh_out)) AS e,
        MAX(s.power_ac) AS pp,
        1000* ( (MAX(e.kwh_in_1) + MAX(e.kwh_in_2) - MAX(b.kwh_in))
        + MAX(s.yield_today)
        - ((MAX(e.kwh_out_1) + MAX(e.kwh_out_2) - MAX(b.kwh_out))) ) AS c
    FROM electricity e
    INNER JOIN baseline b ON b.date = DATE(e.sample)
    LEFT JOIN sems s ON DATE(s.sample) = DATE(e.sample)
    WHERE DATE(e.sample) BETWEEN
        (SELECT d_start::date FROM data_range) AND (SELECT d_end::date FROM data_range)
    GROUP BY DATE(e.sample)

"""

cur.execute(query)
rows = cur.fetchall()

pvoutput = pvoutput.pvoutput(config['pvoutput']['api-key'], config['pvoutput']['site-id'])



for row in rows:
    response = pvoutput.sendDataOutput(data=row)
#    print(f'got response: {response}')


