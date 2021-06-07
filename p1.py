import serial
import re
import configparser
import psycopg2
import datetime

config = configparser.ConfigParser()
config.read('config.ini')



ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE)



mapping_table = {
    #'0.2.8': 'version_info',
    '1.0.0': 'sample',
    '1.7.0': 'power_in',
    '2.7.0': 'power_out',
    '1.8.1': 'kwh_in_1',
    '1.8.2': 'kwh_in_2',
    '2.8.1': 'kwh_out_1',
    '2.8.2': 'kwh_out_2',
    '31.7.0': 'current_l1',
    '51.7.0': 'current_l2',
    '71.7.0': 'current_l3',
    '21.7.0': 'power_in_l1',
    '41.7.0': 'power_in_l2',
    '61.7.0': 'power_in_l3',
    '22.7.0': 'power_out_l1',
    '42.7.0': 'power_out_l2',
    '62.7.0': 'power_out_l3',
    '32.7.0': 'voltage_l1',
    '52.7.0': 'voltage_l2',
    '72.7.0': 'voltage_l3'
}


telegram = []
stop = False
while not stop:
    lines = ser.read(1024).decode('utf-8').split('\n')
    for line in lines:
        # look for first line
        # /KFM5KAIFA-METER
        if len(telegram) == 0 and line[0:4] == '/ISK':
            telegram.append(line)
        if len(telegram) > 0:
            telegram.append(line)
        if len(telegram) > 0 and re.match("^\![A-Z0-9]{4}", line):
            print('stopping')
            stop = True
            break

data = []           
for line in telegram:
    matches = re.match('^\d\-\d\:(\d+\.\d\.\d)\(([0-9\.]*)\*?(.*?)\)', line)
    if matches:
        groups = matches.groups()
        if groups[0] in mapping_table:
            if groups[2]:
                unit = groups[2]
            else:
                unit = ''
 
            value = groups[1]
            if mapping_table[groups[0]] == 'sample':
                # 21 01 16 22 15 32
                value = datetime.datetime(
                        2000+int(value[0:2]),
                        int(value[2:4]),
                        int(value[4:6]),
                        int(value[6:8]),
                        int(value[8:10]),
                        int(value[10:12])
                        )

            data.append({
                'field': groups[0],
                'db': mapping_table[groups[0]],
                'value': value,
                'unit': unit
                })
        else:
            print(f'{groups}')

for d in data:
    print(f"got {d['db']} -> {d['value']}")
# now insert into db
## setup db connection
database = config['database']
username = database['username']
password = database['password']
hostname = database['hostname']
dbname = database['database']

dsn = f"dbname='{dbname}' user='{username}' host='{hostname}' password='{password}'"
try:
    conn = psycopg2.connect(dsn)
except Exception as e:
    print(f'db is b0rken {dsn} / {e}')

cur = conn.cursor()

## prepare query
cols = ','.join([d['db'] for d in data])
placeholders = ','.join(['%s' for d in data])
values = [d['value'] for d in data]
query = f'INSERT INTO electricity ({cols}) VALUES ({placeholders}) ON CONFLICT (sample) DO NOTHING'

for d in data:
    print(f'{d}')

cur.execute(query, values)
conn.commit()

