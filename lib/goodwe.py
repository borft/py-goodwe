import json
import socket
import datetime
from enum import Enum


class GoodweStatus(Enum):
    WAITING = 0
    NORMAL = 1
    ERROR = 2
    CHECKING = 3


def to_16_bit(buffer: [bytes], exp: int = -1, signed: bool = False) -> int:
    return round((int.from_bytes(bytes(buffer), byteorder='big', signed=signed)) * 10**exp, -exp);

class Goodwe:

    _port: int = 0
    _ip: str = ''

    def __init__(self, ip: str = '', port: int = 8899) -> None:
        if ip != '':
            self._ip = ip
        self._port = port

    @staticmethod
    def getCRC(payload: [bytes]) -> [bytes]:
        crc = 0xFFFF
        odd = False
    
        for i in range(0, len(payload)):
            crc ^= payload[i]

            for j in range(0, 8):
                odd = (crc & 0x0001) != 0
                crc >>= 1;
                if odd:
                    crc ^= 0xA001
        return crc.to_bytes(2, byteorder='little', signed=False)

    def getData(self, retries=3):
        while retries > 0:
            retries -= 1
            try:
                return self._getData(self._ip, self._port)
            except Exception as e:
                print(f'Retrying {retries} {e}')
                pass
        raise Exception('Could not get proper data after retrying')

    def _getData(self, ip, port):

        # get data from inverter
        cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cs.settimeout(1)
        msg = bytes(b'\x7f\x03\x75\x94\x00\x49\xd5\xc2')
        cs.sendto(msg, (ip, port))

        response = cs.recvfrom(1024)
        #print(f'Got response from server: {response}')

        # the first part is a list of bytes
        data = bytes(response[0])

        # check length of packet
        if len(data) != 153:
            raise Exception(f'Invalid data (unexpected length: {len(data)}')

        # check header
        header = data[0:2]
        if header != b'\xaa\x55':
            raise Exception(f'Invalid header: {header}')

        # check CRC
        receivedCRC = data[-2:]
        payload = data[2:151]
        calculatedCRC = self.getCRC(payload)
        if receivedCRC != calculatedCRC:
            raise Exception(f'comparing received {receivedCRC} {int.from_bytes(receivedCRC, "big")} to {calculatedCRC}')
            

        # timestamp provided by inverter, internal clock seems to be a bit off
        # so we provide our own timestamp in stead.
        date = datetime.datetime(
            year=data[5] + 2000, month = data[6], day=data[7],
            hour=data[8],minute=data[9], second=data[10])

        print(f'inverter: {date}')

        gw = {
            'sample': datetime.datetime.now(),
            'voltage_dc_1': to_16_bit(data[11:13]),
            'current_dc_1': to_16_bit(data[13:15]),
            'voltage_dc_2': to_16_bit(data[15:17]),
            'current_dc_2': to_16_bit(data[17:19]),
            'voltage_dc_3': to_16_bit(data[19:21]),
            'current_dc_3': to_16_bit(data[21:23]),
            'voltage_dc_4': to_16_bit(data[23:25]),
            'current_dc_4': to_16_bit(data[25:27]),

            'voltage_ac_1': to_16_bit(data[41:43]),
            'voltage_ac_2': to_16_bit(data[43:45]),
            'voltage_ac_3': to_16_bit(data[45:47]),
            'current_ac_1': to_16_bit(data[47:49]),
            'current_ac_2': to_16_bit(data[49:51]),
            'current_ac_3': to_16_bit(data[51:53]),
            'frequency_ac_1': to_16_bit(data[53:55], -2),
            'frequency_ac_2': to_16_bit(data[55:57], -2),
            'frequency_ac_3': to_16_bit(data[57:59], -2),
            'power_ac': to_16_bit(data[61:63], 0),
            'status': GoodweStatus(int(to_16_bit(data[63:65], 0))),

            'temperature': to_16_bit(data[87:89]),
            'yield_today': to_16_bit(data[93:95]),
            'yield_total': to_16_bit(data[95:99]),
            'working_hours': to_16_bit(data[101:103], 0)
        }

        if gw['yield_today'] > 6500:
            raise Exception(f'Yield today too high {gw["yield_today"]}')
        if gw['yield_total'] > 4000000:
            raise Exception(f'yield total too high {gw["yield_total"]}')

        if gw['status'] == GoodweStatus.WAITING:
            # if inverter is in waiting state, yield_today sometimes isn't reset
            # properly, and still has yesterday's value
            gw['yield_totay'] = 0

        # add DC power output if applicable
        for i in range(1,5):
            if gw[f'voltage_dc_{i}'] < 6553:
                gw[f'power_dc_{i}'] = gw[f'voltage_dc_{i}'] * gw[f'current_dc_{i}']

        # remove f2 and f3 ac fields for single phase inverters
        for i in [2,3]:
            good = True
            for field in ['voltage', 'current', 'frequency']:

                gw_field = f'{field}_ac_{i}'
                if gw_field not in gw:
                    continue
                if field == 'voltage' and gw[gw_field] == 6553.5:
                    good = False
                if not good:
                    gw[gw_field] = 0
        return gw

