from datetime import datetime

from config import LOGLEVEL


def error_msg(msg: str) -> None:
    logmsg(msg, 'E')

def info_msg(msg: str) -> None:
    if LOGLEVEL in 'ID':
        logmsg(msg, 'I')


def debug_msg(msg: str) -> None:
    if LOGLEVEL == 'D':
        logmsg(msg, 'D')


def logmsg(msg: str, level: str = 'I') -> None:
    dt = datetime.now()
    sdt = dt.strftime('%Y-%m-%d %H:%M:%S')
    print(f'{sdt} {level} {msg}')
