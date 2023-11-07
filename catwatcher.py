#!/usr/bin/env python3
import sys
from config import STDIN, STDOUT, STDERR, PIDFILE
from catdaemon import CatDaemon

if __name__ == "__main__":
    daemon = CatDaemon(pidfile=PIDFILE, stdin=STDIN, stdout=STDOUT, stderr=STDERR)
    if len(sys.argv) == 2:
        task = sys.argv[1]
        if 'start' == task:
            daemon.start()
        elif 'stop' == task:
            daemon.stop()
        elif 'restart' == task:
            daemon.restart()
        else:
            print('Unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
