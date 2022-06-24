import psycopg2, psycopg2.extras as extras
import time

from homeassistant.components.rest.data import RestData
from homeassistant.components.sensor import (
    DEVICE_CLASS_ENERGY,
    PLATFORM_SCHEMA,
    STATE_CLASS_TOTAL_INCREASING,
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
)
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

import voluptuous as vol


from datetime import timedelta
SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required('username'): cv.string,
        vol.Required('password'): cv.string,
        vol.Required('hostname'): cv.string,
        vol.Required('dbname'): cv.string,
    }
)



    

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):

    sensor_types = ['generation', 'consumption', 'in1', 'in2', 'out1', 'out2']
    sensor_data = CachedSensorData(config=config)


    async_add_entities([DBSensorMeasurement(f'daily_{st}', sensor_data) for st in sensor_types])
    async_add_entities([DBSensorIncreasing(f'total_{st}', sensor_data) for st in sensor_types])

class CachedSensorData:


    def get_cursor(self):
        config = self.config
        username = config.get('username')
        password = config.get('password')
        hostname = config.get('hostname')
        dbname = config.get('dbname')

        dsn = f"dbname='{dbname}' user='{username}' host='{hostname}' password='{password}'"

        conn = psycopg2.connect(dsn, cursor_factory=extras.DictCursor)
        return conn.cursor()



    def __init__(self, config):
        self.config = config

        self._last = 0
        # wait max 10s before new query
        self._max_age = 10

        self.data = {}

        self.update()

    def update(self):
        if time.time() - self._last > self._max_age:
            cursor = self.get_cursor()

            query = '''SELECT 
                    MAX(kwh_in_1) - MIN(kwh_in_1) as daily_in1,
                    MAX(kwh_in_2) - MIN(kwh_in_2) as daily_in2,
                    MAX(kwh_out_1) - MIN(kwh_out_1) as daily_out1,
                    MAX(kwh_out_2) - MIN(kwh_out_2) as daily_out2,
                    MAX(kwh_in_1) as total_in1,
                    MAX(kwh_in_2) as total_in2,
                    MAX(kwh_out_1) as total_out1,
                    MAX(kwh_out_2) as total_out2
                FROM electricity
                WHERE DATE(sample) = DATE(NOW())
                GROUP BY DATE(sample)'''
            cursor.execute(query)
            power_data = {k: v for k,v in cursor.fetchone().items()}
            
            query = '''
                SELECT 
                    COALESCE(MAX(yield_today), 0) as daily_generation
                FROM sems 
                WHERE DATE(sample) = DATE(NOW())'''
            cursor.execute(query)
            solar_daily = cursor.fetchone()
            daily_generation = solar_daily['daily_generation']

            query = """
                SELECT 
                    MAX(yield_total) as total_generation
                FROM sems
                WHERE
                    sample > NOW() - INTERVAL '1 day'

            """
            cursor.execute(query)
            solar_total = cursor.fetchone()
            total_generation = solar_total['total_generation']


            daily_consumption = power_data['daily_in1'] + power_data['daily_in2'] + \
                    daily_generation - \
                    power_data['daily_out1'] - power_data['daily_out2']

            total_consumption = power_data['total_in1'] + power_data['total_in2'] +\
                    total_generation - \
                    power_data['total_out1'] - power_data['total_out2']

            self.data = {**power_data,
                    'daily_generation': daily_generation,
                    'total_generation': total_generation,
                    'daily_consumption': daily_consumption, 
                    'total_consumption': total_consumption}

            self._last = time.time()
            cursor.close()

    def get(self, key: str):
        self.update()
        if key in self.data:
            return self.data[key]
        else:
            raise ValueError(f'Could not find {key}')


class DBSensor(SensorEntity):
    _attr_device_class = DEVICE_CLASS_ENERGY
    _attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, sensor_type: str, data: CachedSensorData):
        self._attr_name = sensor_type
        self.data = data
        self._update()
   
    @callback
    def _update(self):
        self.value = self.data.get(self._attr_name)

    @property
    def native_value(self):
        """Return the state of the device."""
        if self.value:
            return self.value
        return None

    @property
    def unique_id(self) -> str:
        return self._attr_name


    @property
    def extra_state_attributes(self):
        return {}


    async def async_update(self):
        """Get the latest data from the PVOutput API and updates the state."""
        self._update()

    async def async_added_to_hass(self):
        self._update()

class DBSensorIncreasing(DBSensor):

    _attr_state_class = STATE_CLASS_TOTAL_INCREASING
class DBSensorMeasurement(DBSensor):
    
    _attr_state_class = STATE_CLASS_MEASUREMENT
