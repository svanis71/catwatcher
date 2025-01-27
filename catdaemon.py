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
from catlogging import info_msg, debug_msg, error_msg
from config import HISTORY
from history import CatHistory
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
    lights_outdoor_on = False
    lights_on = False
    risehr, risemn = 0, 0
    sethr, setmn = 0, 0

    def __init___(self, pidfile, stdin, stdout, stderr):
        super(CatDaemon, self).__init__(pidfile, stdin, stdout, stderr)

    def display_time(self, time_str):
        self.disp.print_str(time_str)
        self.disp.set_decimal(1, True)
        self.disp.show()

    def turnoff_leds(self):
        self.leds.clear()
        self.leds.show()

    def button_a_handler(self, _):
        self.turnoff_leds()
        latest = self.hist.get_latest()
        debug_msg(f'Latest was {latest}')
        self.display_time(latest)
        self.lights.rgb(1, 0, 0)
        self.lights_on = True

    def button_b_handler(self, _):
        self.turnoff_leds()
        dat = datetime.now()
        time_str = dat.strftime('%H%M')
        debug_msg(f'Current time is {time_str}')
        self.display_time(f'{time_str}')
        self.lights.rgb(0, 1, 0)
        self.lights_on = True

    def callbackfunction(self, deviceId, method, value, callbackId, context):
        dt = datetime.now()
        sdt = dt.strftime('%Y-%m-%d %H:%M:00')
        time_str = dt.strftime('%H%M')

        if deviceId == 7:
            debug_msg(f'callback for deviceId 7 at {sdt} method {method}')
            debug_msg(f'check if event is a duplicate: last was {self.last_event}')
            # For some reason the motion sensor sends the same event twice
            debug_msg(f"\t{sdt} == {self.last_event['time']} -> {sdt == self.last_event['time']}")
            debug_msg(f"\t{deviceId} == {self.last_event['deviceId']} -> {deviceId == self.last_event['deviceId']}")
            debug_msg(f"\t{method} == {self.last_event['method']} -> {method == self.last_event['method']}")
            
            if sdt == self.last_event['time'] and deviceId == self.last_event['deviceId'] and method == self.last_event['method']:
                debug_msg('Event was a duplicate')
                return
            
            debug_msg('Sparar för duplikat')
            self.last_event['time'] = sdt
            self.last_event['method'] = method
            self.last_event['deviceId'] = deviceId

            animation = [(0, 0, 0, 255),
                         (1, 47, 150, 255),
                         (2, 82, 220, 255),
                         (3, 255, 255, 174),
                         (4, 255, 255, 110),
                         (5, 255, 255, 46),
                         (6, 255, 255, 255)
                         ]
            if method == 1:
                debug_msg('Sends event')
                self.send(sdt)
                debug_msg('Visar tiden')
                self.display_time(self.hist.add_history(time_str))
                self.lights.rgb(1, 0, 0)
                self.lights_on = True

                try:
                    if dt.hour <= self.risehr or dt.hour >= self.sethr:
                        debug_msg('Welcome! Turn on the #8 lights')
                        lib.tdTurnOn(8, 3)
                        debug_msg('Reset count down')
                        self.count_down = 3600
                        self.lights_outdoor_on = True
                except Exception as e:
                    error_msg(f'Failed to turn on the lights. {e}')
                
                for lap in range(5):
                    self.leds.clear()
                    for lamp in animation:
                        no, r, g, b = lamp
                        self.leds.set_pixel(no, r, g, b, 0.1)
                        self.leds.show()
                        time.sleep(0.3)
                self.leds.clear()
            if method == 2:
                self.leds.clear()
        self.turnoff_leds()
        sys.stdout.flush()

    def run(self):
        info_msg('Run')
        now = datetime.now()
        seconds_to_suncheck, minute_tick, hour_tick = 0, 60 - now.second, 0
        turnoff_at_sunrise = [1, 2, 4, 5, 6, 8, 10]
        self.touch.A.press(self.button_a_handler)
        self.touch.B.press(self.button_b_handler)
        CMPFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)
        cmp_func = CMPFUNC(self.callbackfunction)
        lib.tdInit()
        lib.tdRegisterDeviceEvent(cmp_func, 0)

        no_problem = True
        while True:
            # if hour_tick == 0:
            #     infomsg(f'Status report {vars(self)}')
            try:
                if no_problem:
                    self.refresh_sunclient(seconds_to_suncheck)
                    self.turn_off_outdoor_lights()
                    self.do_every_minute(minute_tick, turnoff_at_sunrise)
                    if self.lights_on and hour_tick % 600 == 0:
                        debug_msg('Turn off leds')
                        self.button_a_handler(None)
                        self.lights.rgb(0, 0, 0)
                        self.lights_on = False
                else:
                        self.leds.set_pixel(0, 255, 0, 0, 0.1)
                        self.leds.show()
            except Exception as e:
                error_msg(f'Problems with sunset/sunrise or the lights {e}')
                no_problem = False
            self.count_down = self.count_down - 1 if self.count_down >= 0 else -1
            seconds_to_suncheck = (seconds_to_suncheck + 1) % 3600
            minute_tick = (minute_tick + 1) % 60
            hour_tick = (hour_tick + 1) % 60
            time.sleep(1)

    def do_every_minute(self, minute_tick, turnoff_at_sunrise) -> None:
        if minute_tick == 0:
            now = datetime.now()
            now_hr, now_min = now.hour, now.minute
            weekday = now.weekday()

            if now_hr == self.sethr - 1 and now_min == self.setmn:
                for dev in [1, 2, 4, 5, 10]:
                    debug_msg(f'Sunset! Turn the #{dev} lights on')
                    lib.tdTurnOn(dev, 3)
            if now_hr == 5 and now_min == 0 and now_hr <= self.risehr:
                for dev in [1, 2, 4, 5, 10]:
                    debug_msg(f'Good morning! Turn the #{dev} lights on')
                    lib.tdTurnOn(dev, 3)

            if now_hr == self.risehr + 1 and now_min == self.risemn:
                for dev in turnoff_at_sunrise:
                    debug_msg(f'Sunrise! Turn the #{dev} lights off')
                    lib.tdTurnOff(dev, 3)
                self.lights_outdoor_on = False
            if (weekday < 4 and now_hr == 22 and now_min == 30) or (weekday >= 4 and now_hr == 23 and now_min == 30):
                for dev in [1, 2, 4, 5, 10]:
                    debug_msg(f'Good night! Turn the #{dev} lights off')
                    lib.tdTurnOff(dev, 3)

    def turn_off_outdoor_lights(self):
        if self.lights_outdoor_on and self.count_down < 0:
            debug_msg('Turn the #8 lights off')
            lib.tdTurnOff(8, 3)
            self.lights_outdoor_on = False

    def refresh_sunclient(self, seconds_to_suncheck):
        if seconds_to_suncheck == 0:
            self.risehr, self.risemn = self.sunclient.get_sunrise()
            self.sethr, self.setmn = self.sunclient.get_sunset()
            info_msg(f'Sunrise {self.risehr}:{self.risemn} Sunset {self.sethr}:{self.setmn}')

    def send(self, dateString):
        try:
            fname = '/home/pi/code/catwatcher/config.json'
            with open(fname, 'r') as f:
                config = json.load(f)
            url = config['WebService']['PostEventUrl']
            rainbowurl = config['WebService']['RainbowHatUrl']
            apiKey = config['Api']['Key']
            debug_msg(f'Config url={url} key={apiKey}')
            sdt = dateString[0:10]
            sdts = sdt + ' ' + dateString[11:]
            data = {'dateString': f'{sdt}T{dateString[11:]}'}
            debug_msg(f'data {data}')
            now = datetime.now()
            timestamp = now.timestamp()
            if timestamp >= self.expiry_time:
                info_msg(f'Renew authorization token at {now}')
                self.token, self.expiry_time = authorize()

            headers = {
                "Content-Type": "application/json",
                "X-ApiKey": apiKey,
                "Authorization": self.token
            }
            debug_msg(f'Event posted at {sdts}')
            req = requests.post(url=url, data=json.dumps(data), headers=headers)
            if req.ok:
                info_msg(f'Event registered at {sdts}')
            else:
                error_msg(f'Failed to post {data} event at {sdts}')
                error_msg(f'Status: {req.status_code}')
                error_msg(f'Message: {req.text}')
        except Exception as ex:
            error_msg(f'Fel vid skicka {ex}')
