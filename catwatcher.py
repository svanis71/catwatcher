#!/usr/bin/env python

import sys
import ConfigParser
from catdaemon import CatDaemon

if __name__ == "__main__":
    config = ConfigParser.SafeConfigParser()
    config.read('catwatcher.cfg')

    stdoutlog = config.get('Logging', 'stdout')
    stderrlog = config.get('Logging', 'stderr')
    
    daemon = CatDaemon('/tmp/catdaemon.pid', '/dev/null', stdoutlog, stderrlog)
    daemon.url = config.get('WebService', 'url')
    daemon.apiKey = config.get('WebService', 'apiKey')
    
    if len(sys.argv) == 2:
        task = sys.argv[1]
        if 'start' == task:
            daemon.start()
        elif 'stop' == task:
            daemon.stop()
        elif 'restart' == task:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
