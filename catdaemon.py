#!/usr/bin/env python3

from datetime import datetime
import sys, time, platform
import json
import os
import requests
from history import CatHistory
from sunclient import SunClient

#imports allowing the use of our library
from ctypes import c_int, c_ubyte, c_void_p, POINTER, string_at 
from ctypes import cdll, CFUNCTYPE
# The Rainbow HAT api
import rainbowhat as rh

from auth.authorize import authorize
from config import DEVICES_URL, MYAPIKEY, APIKEY_HEADER, HISTORY

SAY_HELLO_TO_CAT_SONG = [    
    # d#E f#G 
    (63, 0.2, 0.3), (64, 0.2, 0.3), (66, 0.2, 0.3), (67, 0.2, 0.6), 
    # d#E f#G
    (63, 0.2, 0.3), (64, 0.2, 0.3), (66, 0.2, 0.3), (67, 0.2, 0.6), 
    # C BEGB a#
    (72, 0.2, 0.3), (83, 0.2, 0.3), (76, 0.2, 0.3), (79, 0.2, 0.3), (83, 0.2, 0.3), (82, 0.2, 0.3),
    # EDBAG E
    (64, 0.2, 0.3), (62, 0.2, 0.3), (71, 0.2, 0.3), (69, 0.2, 0.3), (67, 0.2, 0.3), (64, 0.2, 0.3)]

# Generic Daemon
from daemon import Daemon
# Import the telldus api
lib = cdll.LoadLibrary('libtelldus-core.so.2')
#CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)

def play_pink_panther():
    for (tone, dur, pause) in SAY_HELLO_TO_CAT_SONG:
        rh.buzzer.midi_note(tone, dur)
        time.sleep(pause)

class CatDaemon(Daemon):
    last_event = {'time': '', 'method': -1, 'deviceId': -1}
    token = ''
    expiry_time = -1
    hist = CatHistory(HISTORY)
    sunclient = SunClient()
    disp = rh.display
    leds = rh.rainbow
    touch = rh.touch
    count_down = -1
    lights_on = False
    risehr, risemn = 0, 0
    sethr, setmn = 0, 0

    def __init___(self, pidfile, stdin, stdout, stderr):
        super(CatDaemon, self).__init__(pidfile, stdin, stdout, stderr)
        
    def button_a_handler(self, _):
        self.leds.clear()
        self.leds.show()
        latest = self.hist.get_latest()
        print(f'Latest was {latest}')
        self.disp.print_str(latest)
        self.disp.set_decimal(1, True)
        self.disp.show()

    def button_b_handler(self, _):
        self.leds.clear()
        self.leds.show()
        prev = self.hist.get_prev()
        print(f'Prev was {prev}')
        self.disp.print_str(prev)
        self.disp.set_decimal(1, True)
        self.disp.show()

    def button_c_handler(self, _):
        self.leds.clear()
        self.leds.show()
        next = self.hist.get_next()
        print(f'Next was {next}')
        self.disp.print_str(next)
        self.disp.set_decimal(1, True)
        self.disp.show()

    def callbackfunction(self, deviceId, method, value, callbackId, context):
        dt = datetime.now()
        sdt = dt.strftime('%Y-%m-%d %H:%M:00')
        time_str = dt.strftime('%H%M')

        # For some reason the motion sensor sends the same event twice
        if sdt == self.last_event['time'] and deviceId == self.last_event['deviceId'] and method == self.last_event['method']:
            return
        self.last_event['time'] = sdt
        self.last_event['method'] = method
        self.last_event['deviceId'] = deviceId

        if deviceId == 7:
            animation = [(0, 255, 0, 0, 0.1),
                         (1, 0, 255, 0, 0.1),
                         (2, 0, 0, 255, 0.1),
                         (3, 255, 255, 0, 0.1),
                         (4, 0, 255, 255, 0.1),
                         (5, 255, 0, 255, 0.1),
                         (6, 128, 255, 128, 0.1)
            ]
            if method == 1:
                self.send(sdt)
                self.disp.print_str(self.hist.add_history(time_str))
                self.disp.set_decimal(1, True)
                self.disp.show()
                for lap in range(7):
                    self.leds.clear()
                    for lamp in animation:
                        (no, r, g, b, l) = lamp
                        self.leds.set_pixel(no, r, g, b, 0.1)
                        self.leds.show()
                        time.sleep(0.3)
                self.leds.clear()
                try:
                    if (dt.hour <= self.risehr or dt.hour >= self.sethr) and self.count_down < 0:
                        print('Turn on the lights') 
                        lib.tdTurnOn(8, 3)
                        self.count_down = 3600
                        self.lights_on = True
                except Exception as e:
                    print(f'Failed to turn on the lights. {e}')
            if method == 2:
                self.leds.clear()
        self.leds.clear()
        self.leds.show()
        sys.stdout.flush()
                    
    def run(self):
        print('Run')
        secondsToSuncheck, minute_tick = 0, 0
        self.touch.A.press(self.button_a_handler)
        self.touch.B.press(self.button_b_handler)
        self.touch.C.press(self.button_c_handler)
        CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)
        cmp_func = CMPFUNC(self.callbackfunction)
        lib.tdInit()
        lib.tdRegisterDeviceEvent(cmp_func, 0)

        no_problem = True
        while True:
            try:
                if no_problem:
                    if secondsToSuncheck == 0:
                        self.risehr, self.risemn = self.sunclient.get_sunrise()
                        self.sethr, self.setmn = self.sunclient.get_sunset()
                        print(f'Sunrise {self.risehr}:{self.risemn} Sunset {self.sethr}:{self.setmn}')
                    secondsToSuncheck = (secondsToSuncheck + 1) % 3600
                    self.count_down = self.count_down - 1 if self.count_down >= 0 else -1
                    if self.lights_on and self.count_down < 0:
                        print('Turn the #8 lights off')
                        lib.tdTurnOff(8, 3)
                        self.lights_on = False
                    if minute_tick == 0:
                        now = datetime.now()
                        now_hr, now_min = now.hour, now.minute
                        if now_hr == self.sethr and now_min == self.setmn:
                            print('Turn the #4 lights on')
                            lib.tdTurnOn(4, 3)
                        if now_hr == self.risehrhr and now_min == self.risemnmn:
                            print('Turn the #4 lights on')
                            lib.tdTurnOff(4, 3)
            except Exception as e:
                print(f'Problems with sunset/sunrise or the lights {e}')
                no_problem = False
            time.sleep(1)

    def send(self, dateString):
        fname = '/home/pi/code/catwatcher/config.json'
        with open(fname, 'r') as f:
            config = json.load(f)
        url = config['WebService']['PostEventUrl']
        rainbowurl = config['WebService']['RainbowHatUrl']
        apiKey = config['Api']['Key']
        sdt = dateString[0:10]
        sdts = sdt + ' ' + dateString[11:]
        data = {'dateString': f'{sdt}T{dateString[11:]}'}

        now = datetime.now()
        timestamp = now.timestamp()
        if timestamp >= self.expiry_time:
            print('Renew authorization token at', now)
            self.token, self.expiry_time = authorize()
        
        headers = {
            "Content-Type": "application/json",
            "X-ApiKey": apiKey,
            "Authorization": self.token
        }
        print('Event registered at ', sdts)
        req = requests.post(url=url, data=json.dumps(data), headers=headers)
        if req.ok:
            print('Event registered at ', sdts)
        else:
            print(f'Failed to post {data} event at {sdts}')
            print('Status: ', req.status_code)
            print('Message: ', req.text)
