import http.client
import json
from datetime import datetime

from config import GET_TOKEN_HOST, CLIENT_ID, CLIENT_SECRET, AUDIENCE


def authorize():
    conn = http.client.HTTPSConnection(GET_TOKEN_HOST)
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'audience': AUDIENCE,
        'grant_type': 'client_credentials'
    }
    
    headers = {'content-type': "application/json"}
    conn.request("POST", "/oauth/token", json.dumps(payload), headers)
    res = conn.getresponse()
    data = res.read()
    auth_info = json.loads(data.decode('utf-8'))
    token = '%s %s' % (auth_info['token_type'], auth_info['access_token'])
    now = datetime.now().timestamp()
    expiry_time = now + auth_info['expires_in']
    return token, expiry_time
