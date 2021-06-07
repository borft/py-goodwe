# py-goodwe
Python based lib to locally read data from Goodwe inverters.


# CREDITS
Heavily inspired  by work from Sircuri here: https://github.com/sircuri/GoodWeUSBLogger



# How to use
Basically all of the magic is in goodwe.py, it queries the inverter, and returns a dictionary
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

# PVOutput support
As a bonus, there's also some support for pvoutput, and a local db:
- copy config.ini.dist to config.ini, and populate (inverter settings, db credentials and pvoutput api key)
- `run.py` will fetch data from the inverter and store it in the local db
- `push_status.py` and `push_output.py` will push your data to pvoutput
- `p1.py` can read, parse and insert p1 data from a smart electricity meter
- db structure is in db.sql

