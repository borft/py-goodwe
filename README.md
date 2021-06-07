# py-goodwe
Python based lib to locally read data from Goodwe inverters.


# CREDITS
Heavily inspired by koen-lee: https://github.com/koen-lee/GoodweUDPToPvOutput/tree/main/GoodweUdpPoller



# How to use
Basically all of the magic is in `goodwe.py`, it queries the inverter, and returns a dictionary
containing whatever it can gather. Should support up to 4 MPPT, but tested on my own with 2, YMMV ;)


# Example:
```python
from goodwe import Goodwe,GoodweStatus

ip = your_ip_here
gw = Goodwe(ip=ip)

try:
    data = gw.getData()
except Exception as e:
    print(f"failed: {e}")
    exit(0)

print(data)

```

Output would look something like this:
```json
{
    "sample": "2021-06-07 16:04:32",
    "voltage_dc_1": 367.0,
    "current_dc_1": 0.6,
    "voltage_dc_2": 542.9,
    "current_dc_2": 9.3,
    "voltage_dc_3": 6553.5,
    "current_dc_3": 6553.5,
    "voltage_dc_4": 6553.5,
    "current_dc_4": 6553.5,
    "voltage_ac_1": 236.3,
    "voltage_ac_2": 233.8,
    "voltage_ac_3": 234.6,
    "current_ac_1": 7.2,
    "current_ac_2": 7.2,
    "current_ac_3": 7.4,
    "frequency_ac_1": 50.01,
    "frequency_ac_2": 50.0,
    "frequency_ac_3": 50.0,
    "power_ac": 5161,
    "status": "NORMAL",
    "temperature": 54.2,
    "yield_today": 36.0,
    "yield_total": 3348.7,
    "working_hours": 2052,
    "power_dc_1": 220.2,
    "power_dc_2": 5048.97,
    "net_frequency_1": 50.01,
    "net_frequency_2": 50.0,
    "net_frequency_3": 50.0
}
```

# PVOutput support
As a bonus, there's also some support for pvoutput, and a local db:
- copy config.ini.dist to config.ini, and populate (inverter settings, db credentials and pvoutput api key)
`run.py` will fetch data from the inverter and store it in the local db:
```bash
PYTHONPATH=.:$PYTHONPATH python scripts/run.py
```
- `push_status.py` and `push_output.py` will push your data to pvoutput and can be run similarly, requirement is to have `psycopg2` installed
- `p1.py` can read, parse and insert p1 data from a smart electricity meter
- db structure is in db.sql

## setup Postgres
Easiest, is to run it in a docker container:

```
docker start postgresql

