#!/usr/bin/env python

from datetime import datetime
import sys, time, platform
import json, urllib2
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
    num_leds = 0
    last_event = ''
    url = 'http://localhost/api/Doorbell'
    apiKey = 'the key'

    def __init___(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.url = 'http://localhost/api/Doorbell'
        self.apiKey = 'dummy key'
        super(CatDaemon, self).__init__(pidfile, stdin, stdout, stderr)
        
    @property
    def url(self):
        return self.url
    
    @url.setter
    def url(self, value):
        self.url = value

    @property
    def apiKey(self):
        return self.apiKey
    
    @apiKey.setter
    def apiKey(self, value):
        self.apiKey = value
        
    def set_leds(self):
        self.num_leds += 1
        for led in range(6):
            backlight.graph_set_led_state(led, self.num_leds & (1 << led))
    
    def callbackfunction(self, deviceId, method, value, callbackId, context):
        dt = datetime.now()
        sdt = dt.strftime('%Y-%m-%d %H:%M')
        # For some reason the motion sensor sends the same event twice
        if(sdt == self.last_event):
            return
        self.last_event = sdt
        if(deviceId == 7):
            if(method == 1):
                lcd.clear()
                lcd.set_cursor_position(0, 0)
                lcd.write(sdt)
                backlight.rgb(0, 255, 0)
                self.set_leds()
                self.send(sdt)
                print sdt
            if(method == 2):
                lcd.set_cursor_position(0, 1)
                lcd.write('Waiting...')
                backlight.off()
            sys.stdout.flush()
                    
    def run(self):
        CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)
        cmp_func = CMPFUNC(self.callbackfunction)
        lib.tdInit()
        lib.tdRegisterDeviceEvent(cmp_func, 0)

        lcd.clear()
        lcd.set_cursor_position(0, 1)
        lcd.write('Waiting...')
        backlight.off()
        backlight.graph_off()

        print 'Started'
        while True:
            time.sleep(1)

    def send(self, dateString):
        data = '{ DeviceId: 7, EventDate: \'' +  dateString + '\' }'
        
        req = urllib2.Request(self.url)
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-ApiKey', self.apiKey)

        response = urllib2.urlopen(req, data)
    
