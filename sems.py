import json
import requests
from typing import Dict, List
from datetime import datetime

class Sems:

    _defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'token': '{"version":"12","client":"android","language":"en"}',
    }

    _urls: Dict = {
        'chart_by_plant': 'https://www.semsportal.com/GopsApi/Post?s=v2/Charts/GetChartByPlant',
        'login': 'https://www.semsportal.com/api/v1/Common/CrossLogin',
        'powerstation': 'https://www.semsportal.com/api/v1/PowerStation/GetMonitorDetailByPowerstationId',
        'login_v2': 'https://www.semsportal.com/Home/Login'
    }

    _session: Dict = {}
    _session_v2: Dict = {}

    _username: str = ''
    _password: str = ''
    _station_id: str = ''

    def __init__(self, username, password, station_id):
        self._username = username
        self._password = password
        self._station_id = station_id

    def _doLoginV2(self) -> Dict:
        login_data = {
                'account': self._username,
                'pwd': self._password
        }
        response = self._request(url=self._urls['login_v2'], headers=self._defaultHeaders, data=login_data)
        self._session_v2 = response
        print(f'login_V2: {response.text}')


    def _doLogin(self) -> Dict:
        # Prepare Login Data to retrieve Authentication Token
        login_data = json.dumps({
            'account': self._username,
            'pwd': self._password
            })
        raw_response = self._request(url=self._urls['login'], headers=self._defaultHeaders, data=login_data)
        response = raw_response

        return {k: v for k, v in response['data'].items() if k in ['timestamp', 'uid', 'token']}


    def getSession(self) -> {}:
        if not self._session:
            self._session = self._doLogin()
        return self._session


    def getChartByPlant(self, chart: int=1, date=datetime.now().strftime('%Y-%m-%d')) -> Dict:
        session = self.getSession()
        headers = self._defaultHeaders
        headers['token'] = json.dumps({
            'version': '12',
            'client': 'android',
            'language': 'en',
            'timestamp': str(session['timestamp']),
            'uid': session['uid'],
            'token': session['token']
            })
        
        # get chart data
        data = {
            "str": {
                "api":"v2/Charts/GetChartByPlant",
                "param":{
                    "id": self._station_id,
                    "date": date,
                    "range":2,
                    "chartIndexId": chart,
                    "isDetailFull":""
                    }
                }
            }
        return self._request(url=self._urls['chart_by_plant'], headers=headers, data=json.dumps(data))


    def getPowerStation(self) -> {}:
        session = self.getSession()
        headers = self._defaultHeaders
        headers['token'] = json.dumps({
            'version': '12',
            'client': 'android',
            'language': 'en',
            'timestamp': str(session['timestamp']),
            'uid': session['uid'],
            'token': session['token']
            })
        data = json.dumps({'powerStationId': self._station_id})
        
        return self._request(url=self._urls['powerstation'], headers=headers, data=data)

    def _request(self, url: str, headers: [], data: []) -> {}:
        # Prepare Login Headers to retrieve Authentication Token
        print(f'Sending post request with payload: "{data}"')
        response = requests.post(url, headers=headers, data=data)
        return response



