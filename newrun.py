from sems import Sems
import json
import configparser
import psycopg2
import datetime

## read config / ini file
config = configparser.ConfigParser()
config.read('db.ini')

## mapping json stream fields
mapping = {
    'sample': 'last_time',
    'current_dc_1': 'ipv1',
    'current_dc_2': 'ipv2',
    'voltage_dc_1': 'vpv1',
    'voltage_dc_2': 'vpv2',
    'power_dc_1': 'ppv1',
    'power_dc_2': 'ppv2',
    'current_ac_1': 'iac1',
    'current_ac_2': 'iac2',
    'current_ac_3': 'iac3',
    'voltage_ac_1': 'vac1',
    'voltage_ac_2': 'vac2',
    'voltage_ac_3': 'vac3',
    'power_ac': 'pac',
    'yield_today': 'eday',
    'yield_total': 'etotal',
    'net_frequency_1': 'fac1',
    'net_frequency_2': 'fac2',
    'net_frequency_3': 'fac3',
    'temperature': 'tempperature'
        }


s = Sems(
        username=config['sems']['username'],
        password=config['sems']['password'],
        station_id=config['sems']['station_id'])

s._doLoginV2()

exit(1)

station = s.getPowerStation()
print(f'station: {station}')

plant = s.getChartByPlant()
print(f'plang: {plant}')

print(f'{json.dumps(data)}')

for db_field, json_field in mapping.items():
    if db_field == 'power_dc_1':
        data[json_field] = data['vpv1'] * data['ipv1']
    if db_field == 'power_dc_2':
        data[json_field] = data['vpv2'] * data['ipv2']
    if db_field == 'sample' and (json_field in data):
        data[json_field] = datetime.datetime.fromtimestamp(int(data[json_field])/1000)
    if json_field in data:
        print(f'Got {json_field}: {data[json_field]} (db:{db_field})')
    else:
        print(f'Missin field in JSON :( {json_field} / {data}')
        exit(1)

if len(data) < 2:
    print('No data :(')
    exit(0)

## setup db connection
database = config['database']
username = database['username']
password = database['password']
hostname = database['hostname']
dbname = database['database']

dsn = f"dbname='{dbname}' user='{username}' host='{hostname}' password='{password}'"
try:
    conn = psycopg2.connect(dsn)
except:
    print('db is b0rken')

cur = conn.cursor()

## prepare query
cols = ','.join(mapping.keys())
placeholders = ','.join(['%s' for m in mapping.values()])
values = [data[key] for key in mapping.values()]
query = f'INSERT INTO sems ({cols}) VALUES ({placeholders}) ON CONFLICT (sample) DO NOTHING'

cur.execute(query, values)
conn.commit()


