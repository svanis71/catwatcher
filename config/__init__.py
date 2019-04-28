from os import path

HOME = '.'
MYAPIKEY=''
APIKEY_HEADER = ''
DEVICES_URL = ''
GET_TOKEN_HOST = ''
CLIENT_ID = ''
CLIENT_SECRET = ''
AUDIENCE = ''

REDIS_URL = ''
PIDFILE = path.join(HOME, 'pytimerd.pid')
STDIN = '/dev/null'
STDOUT = path.join(HOME, 'log', 'stdout.log')
STDERR = path.join(HOME, 'log', 'stderr.log')

try:
    from .runtime_conf import *
except ImportError:
    pass
