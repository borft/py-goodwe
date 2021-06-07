import urllib
import math
from typing import Dict



class pvoutput:

    _urls: Dict = {
            'status': 'https://pvoutput.org/service/r2/addbatchstatus.jsp',
            'output': 'https://pvoutput.org/service/r2/addoutput.jsp'
            }

    _headers: Dict = {}

    def __init__(self, api_key, site_id):
        self._headers = {
            'X-Pvoutput-Apikey': api_key,
            'X-Pvoutput-SystemId': site_id
            }



    # and now, push it!
    def _sendRequest(self, url: str, data: []) -> str:
        request = urllib.request.Request(url=url, headers=self._headers)

        post_data = urllib.parse.urlencode(data)
        post_data = post_data.encode('ascii')
        try:
            return urllib.request.urlopen(request, post_data)
        except Exception as e:
            print(f'caught: {e}')
            print(f'{e.read().decode("utf-8")}')
    

    def _chunkData(self, data: [], max=30) -> [[]]:
        count = math.ceil(len(data)/max)

        for i in range(0, count):
            start = i * max
            stop = start + max

            print(f'sending request for slice start:{start}, stop{stop}')
            yield data[start:stop]
    


    def sendDataStatus(self, data: []) -> []:
            url = self._urls['status']
            for chunk in self._chunkData(data):
                data_str = ';'.join(chunk)
                yield self._sendRequest(url=url, data={'data': data_str})
            
    def sendDataOutput(self, data: []):
        url = self._urls['output']
        print(f'Sending day total output for {data["d"]}')
        return self._sendRequest(url=url, data=data)
