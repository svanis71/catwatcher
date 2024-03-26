#!/usr/bin/env python3

import json
import sys
import time
# imports allowing the use of our library
from ctypes import c_int, c_ubyte, c_void_p, POINTER
from ctypes import cdll, CFUNCTYPE
from datetime import datetime

# The Rainbow HAT api
import rainbowhat as rh
import requests

from auth.authorize import authorize
from config import HISTORY
from history import CatHistory
from catlogging import logmsg
from sunclient import SunClient

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


# CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)

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
    lights = rh.lights
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
        # logmsg(f'Latest was {latest}')
        self.disp.print_str(latest)
        self.disp.set_decimal(1, True)
        self.disp.show()
        self.lights.rgb(1, 0, 0)

    def button_b_handler(self, _):
        self.leds.clear()
        self.leds.show()
        prev = self.hist.get_prev()
        # logmsg(f'Prev was {prev}')
        self.disp.print_str(prev)
        self.disp.set_decimal(1, True)
        self.disp.show()
        self.lights.rgb(1, 0, 0)

    def button_c_handler(self, _):
        self.leds.clear()
        self.leds.show()
        next = self.hist.get_next()
        # logmsg(f'Next was {next}')
        self.disp.print_str(next)
        self.disp.set_decimal(1, True)
        self.disp.show()
        self.lights.rgb(1, 0, 0)

    def callbackfunction(self, deviceId, method, value, callbackId, context):
        dt = datetime.now()
        sdt = dt.strftime('%Y-%m-%d %H:%M:00')
        time_str = dt.strftime('%H%M')

        if deviceId == 7:
            # logmsg(f'callback for deviceId 7 at {sdt} method {method} value {value} callbackId {callbackId}')
            # logmsg(f'check if event is a duplicate last was {self.last_event}')
            # For some reason the motion sensor sends the same event twice
            if sdt == self.last_event['time'] and deviceId == self.last_event['deviceId'] and method == self.last_event['method']:
                logmsg('Event was a duplicate')
                return
            self.last_event['time'] = sdt
            self.last_event['method'] = method
            self.last_event['deviceId'] = deviceId

            animation = [(0, 0, 0, 0xFF),
                         (1, 0x2F, 0x8D, 0xFF), 
                         (2, 0x52, 0xDB, 0xFF),
                         (3, 0xFF, 0xFF, 0xAD),
                         (4, 0xFF, 0xFF, 0x6E), 
                         (5, 0xFF, 0xFF, 0x2E), 
                         (6, 0xFF, 0xFF, 0xFF)
                         ]
            if method == 1:
                self.send(sdt)
                self.disp.print_str(self.hist.add_history(time_str))
                self.disp.set_decimal(1, True)
                self.disp.show()
                try:
                    if dt.hour <= self.risehr or dt.hour >= self.sethr:
                        logmsg('Welcome! Turn on the #8 lights')
                        lib.tdTurnOn(8, 3)
                        logmsg('Reset count down')
                        self.count_down = 3600
                        self.lights_on = True
                except Exception as e:
                    logmsg(f'Failed to turn on the lights. {e}', 'E')
                for lap in range(2):
                    self.leds.clear()
                    for lamp in animation:
                        (no, r, g, b) = lamp
                        self.leds.set_pixel(no, r, g, b)
                        self.leds.show()
                        time.sleep(0.3)
                self.leds.clear()
            if method == 2:
                self.leds.clear()
        self.leds.clear()
        self.leds.show()
        sys.stdout.flush()


    def run(self):
        logmsg('Run')
        now = datetime.now()
        seconds_to_suncheck, minute_tick, hour_tick = 0, 60 - now.second, 0
        turnoff_at_sunrise = [1, 2, 4, 5, 6, 8]
        self.touch.A.press(self.button_a_handler)
        self.touch.B.press(self.button_b_handler)
        self.touch.C.press(self.button_c_handler)
        CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)
        cmp_func = CMPFUNC(self.callbackfunction)
        lib.tdInit()
        lib.tdRegisterDeviceEvent(cmp_func, 0)

        no_problem = True
        toggle_disp = 1
        while True:
            # if hour_tick == 0:
            #     logmsg(f'Status report {vars(self)}')
            try:
                if no_problem:
                    if seconds_to_suncheck == 0:
                        self.risehr, self.risemn = self.sunclient.get_sunrise()
                        self.sethr, self.setmn = self.sunclient.get_sunset()
                        logmsg(f'Sunrise {self.risehr}:{self.risemn} Sunset {self.sethr}:{self.setmn}')
                    if self.lights_on and self.count_down < 0:
                        logmsg('Turn the #8 lights off')
                        lib.tdTurnOff(8, 3)
                        self.lights_on = False
                    if minute_tick == 0:
                        now = datetime.now()
                        now_hr, now_min = now.hour, now.minute
                        if toggle_disp == 1:
                            self.disp.print_str(f'{now_hr}{now_min}')
                            self.disp.set_decimal(1, True)
                            self.disp.show()
                            self.lights.rgb(0, 1, 0)
                        else:
                            self.button_a_handler(0)
                        toggle_disp = (toggle_disp + 1) % 2

                        if now_hr == self.sethr and now_min == 0:
                            for dev in [1, 2, 4, 5, 6]:
                                logmsg(f'Sunset! Turn the #{dev} lights on')
                                lib.tdTurnOn(dev, 3)
                        elif now_hr == 5 and now_min == 0:
                            for dev in [1, 2, 5]:
                                logmsg(f'Good morning! Turn the #{dev} lights on')
                                lib.tdTurnOn(dev, 3)

                        if now_hr == self.risehr and now_min == self.risemn:
                            for dev in turnoff_at_sunrise:
                                logmsg(f'Sunrise! Turn the #{dev} lights off')
                                lib.tdTurnOff(dev, 3)
                            self.lights_on = False
                        elif now_hr == 22 and now_min == 30:
                            for dev in [1, 2, 5]:
                                logmsg(f'Good night! Turn the #{dev} lights off')
                                lib.tdTurnOff(dev, 3)
                                
            except Exception as e:
                logmsg(f'Problems with sunset/sunrise or the lights {e}', 'E')
                no_problem = False
            self.count_down = self.count_down - 1 if self.count_down >= 0 else -1
            seconds_to_suncheck = (seconds_to_suncheck + 1) % 3600
            minute_tick = (minute_tick + 1) % 60
            hour_tick = (hour_tick + 1) % 60
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
            logmsg('Renew authorization token at', now)
            self.token, self.expiry_time = authorize()

        headers = {
            "Content-Type": "application/json",
            "X-ApiKey": apiKey,
            "Authorization": self.token
        }
        logmsg(f'Event posted at {sdts}')
        req = requests.post(url=url, data=json.dumps(data), headers=headers)
        if req.ok:
            logmsg(f'Event registered at {sdts}')
        else:
            logmsg(f'Failed to post {data} event at {sdts}', 'E')
            logmsg(f'Status: {req.status_code}', 'E')
            logmsg(f'Message: {req.text}', 'E')
