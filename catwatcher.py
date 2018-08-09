#!/usr/bin/env python3
import sys, json
from catdaemon import CatDaemon

if __name__ == "__main__":
    with open('config.json', 'r') as f:
        config = json.load(f)
    stdout = config['Logging']['stdout']
    stderr = config['Logging']['stderr']
    daemon = CatDaemon('/tmp/catdaemon.pid', stdout=stdout, stderr=stderr, stdin='/dev/null')
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
