from datetime import datetime


def logmsg(msg: str, level: str = 'I') -> None:
    dt = datetime.now()
    sdt = dt.strftime('%Y-%m-%d %H:%M:%S')
    print(f'{sdt} {level} {msg}')
