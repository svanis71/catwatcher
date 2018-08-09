#!/usr/bin/env python3

from datetime import datetime
import sys, time, platform
import json
import os
import requests

#imports allowing the use of our library
from ctypes import c_int, c_ubyte, c_void_p, POINTER, string_at 
from ctypes import cdll, CFUNCTYPE
# The Display-o-Tron HAT api
import dothat.lcd as lcd
import dothat.backlight as backlight
# Generic Daemon
from daemon import Daemon
# Import the telldus api
lib = cdll.LoadLibrary('libtelldus-core.so.2')
#CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)

class CatDaemon(Daemon):
    last_event = {'time': '', 'method': -1, 'deviceId': -1}
    
    def __init___(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        super(CatDaemon, self).__init__(pidfile, stdin, stdout, stderr)
        
    def callbackfunction(self, deviceId, method, value, callbackId, context):
        dt = datetime.now()
        sdt = dt.strftime('%Y-%m-%d %H:%M')
        
        # For some reason the motion sensor sends the same event twice
        if sdt == self.last_event['time'] and deviceId == self.last_event['deviceId'] and method == self.last_event['method']:
            return
        self.last_event['time'] = sdt
        self.last_event['method'] = method
        self.last_event['deviceId'] = deviceId
        
        if deviceId == 7:
            if method == 1:
                lcd.clear()
                lcd.set_cursor_position(0, 0)
                lcd.write(sdt)
                backlight.rgb(100, 255, 100)
                self.send(sdt)
            if method == 2:
                lcd.clear()
                backlight.off()
                lcd.set_cursor_position(0, 1)
                lcd.write('Waiting for')
                lcd.set_cursor_position(0, 2)
                lcd.write('Smilla to knock')
        sys.stdout.flush()
                    
    def run(self):
        CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)
        cmp_func = CMPFUNC(self.callbackfunction)
        lib.tdInit()
        lib.tdRegisterDeviceEvent(cmp_func, 0)

        lcd.clear()
        lcd.set_cursor_position(0, 1)
        lcd.write('Waiting for')
        lcd.set_cursor_position(0, 2)
        lcd.write('Smilla to knock')
        backlight.off()
        backlight.graph_off()

        print('Started')
        while True:
            time.sleep(1)

    def send(self, dateString):
        fname = '/home/pi/code/catwatcher/config.json'
        with open(fname, 'r') as f:
            config = json.load(f)
        url = config['WebService']['PostEventUrl']
        rainbowurl = config['WebService']['RainbowHatUrl']
        apiKey = config['Api']['Key']
        sdt = dateString[0:10]
        sdts = sdt + ' ' + dateString[11:17]+':00'
        data = {'dateString': sdts}
        headers = {
            "Content-Type": "application/json",
            "X-ApiKey": apiKey
        }
        req = requests.post(url=url, data=json.dumps(data), headers=headers)
        if req.ok:
            print('Event registered at ', sdts)
        else:
            print('Failed to post event at ', sdts)
            print('Status: ', req.status_code)
            print('Message: ', req.text)
