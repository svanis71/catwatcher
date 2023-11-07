from datetime import datetime
from http.client import HTTPSConnection
import json
from os.path import join
from config import HOME

WS_URL = 'www.fam-svanstrom.se'
WS_PATH = '/api/sun/lat/56.21227/lng/15.542849'
SUNRC = join(HOME, '.latestsuncheck')

"""
    File format:

    {"Date": "2023-03-06", "Sunset": "17:42", "Sunrise": "06:38"}

"""
class SunClient:
    def get_sunset(self):
        with open(SUNRC, "r") as sunfile:
            latest_json = sunfile.readline()
        latest = json.loads(latest_json.strip())
        today = datetime.now().strftime('%Y-%m-%d')
        if today != latest["Date"]:
            latest = self.update_from_ws()
        return [int(x) for x in latest["Sunset"].split(':')]

    def get_sunrise(self):
        with open(SUNRC, "r") as sunfile:
            latest_json = sunfile.readline()
        latest = json.loads(latest_json.strip())
        today = datetime.now().strftime('%Y-%m-%d')
        if today != latest["Date"]:
            latest = self.update_from_ws()
        return [int(x) for x in latest["Sunrise"].split(':')]

    def update_from_ws(self):
        conn = HTTPSConnection(WS_URL)
        conn.request('GET', WS_PATH)
        res = conn.getresponse()
        data = res.read()
        with open(SUNRC, "w") as sunfile:
            sunfile.write(data.decode('utf-8'))
        return json.loads(data.decode('utf-8'))
