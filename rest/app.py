from flask import Flask, make_response
from flask_cors import CORS

import configparser, psycopg2, psycopg2.extras as extras
import os
import json 
import datetime
import decimal
from typing import Dict

config = configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/../config.ini')

database = config['database']
username = database['username']
password = database['password']
hostname = database['hostname']
dbname = database['database']

dsn = f"dbname='{dbname}' user='{username}' host='{hostname}' password='{password}'"

try:
    conn = psycopg2.connect(dsn, cursor_factory=extras.DictCursor)
except Exception as e:
    print(f'db is b0rken {e}')
    exit(1)
cur = conn.cursor()

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(MyEncoder, self).default(obj)

def json_encode(data: Dict) -> str:
    encoder = MyEncoder()
    return encoder.encode(data)

app = Flask(__name__)


CORS(app,
    resources={r'/*': {
        'origins': '*',
        'supports_credentials': True,  # needed for cookies
        # Setting max_age to a higher values is probably useless, as most browsers cap this time.
        # See https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Max-Age
        'max_age': 3600 * 24
        }})



@app.route("/")
def index():


    data = _get_response()
    for d in data:
        print(d)
        print(json_encode(d))
    return "hello"

@app.route("/json")
def json():
    response =json_encode(_get_response())

    return make_response(response, 200, {"Content-type": "application/json"})


def _get_response():
    query = f'SELECT * FROM sems s WHERE DATE(s.sample) = DATE(NOW())'
    cur.execute(query)
    rows = cur.fetchall()
    result = []
    for row in rows:
        result.append({k:v for k,v in row.items()})
    return result


if __name__ == "__main__":
    app.run()

