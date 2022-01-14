from lib.goodwe import Goodwe,GoodweStatus
import json
import configparser
import psycopg2
import datetime

## read config / ini file
config = configparser.ConfigParser()
config.read('config.ini')

ip = config['goodwe']['ip']
port = int(config['goodwe']['port'])
gw = Goodwe(ip, port)

try:
    data = gw.getData()
except Exception as e:
    print(f"failed: {e}")
    exit(0)

for i in range(1,4):
    data[f'net_frequency_{i}'] = data[f'frequency_ac_{i}']


if len(data) < 2:
    print('No data :(')
    exit(0)

## setup db connection
database = config['database']
username = database['username']
password = database['password']
hostname = database['hostname']
dbname = database['database']

db_fields = [
    'sample',
    'voltage_dc_1',
    'voltage_dc_2',
    'current_dc_1',
    'current_dc_2',
    'power_dc_1',
    'power_dc_2',
    'voltage_ac_1',
    'voltage_ac_2',
    'voltage_ac_3',
    'current_ac_1',
    'current_ac_2',
    'current_ac_3',
    'power_ac',
    'net_frequency_1',
    'net_frequency_2',
    'net_frequency_3',
    'temperature',
    'yield_today',
    'yield_total'
        ]

# only add fields we have data for
db_fields = [f for f in db_fields if f in data]

# pretty printer
def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
    if isinstance(o, GoodweStatus):
        return o.name
print(json.dumps(data, indent=4, default=myconverter))


dsn = f"dbname='{dbname}' user='{username}' host='{hostname}' password='{password}'"
try:
    conn = psycopg2.connect(dsn)
except:
    print('db is b0rken')

cur = conn.cursor()

## prepare query
cols = ','.join(db_fields)
placeholders = ','.join(['%s' for m in db_fields])
values = [data[key] for key in db_fields]
query = f'INSERT INTO sems ({cols}) VALUES ({placeholders}) ON CONFLICT (sample) DO NOTHING'
cur.execute(query, values)
conn.commit()


