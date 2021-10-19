import os
import threading

from config import Config

from views.poweroff_view import PoweroffView
from views.switch_view import SwitchView
from views.network_view.network_view import NetworkMonitor
from views.test_view.test_view import TestView
from views.iss_view.iss_view import ISSView
from views.weather_view.weather_view import WeatherView

class ViewHandler():
    MODES = [
        "timed",
        "manual",
    ]

    def __init__(self, matrix, press_event, long_press_event):
        self._matrix = matrix
        self._press_event = press_event
        self._long_press_event = long_press_event

        self._mode = Config.read_key("mode")
        self._auto_switch = True

    def start(self):
        poweroffview = PoweroffView(self._matrix, self._press_event, self._long_press_event)
        switchview = SwitchView(self._matrix, self._press_event, self._long_press_event)

        weatherview = WeatherView(self._matrix, self._press_event)
        networkmanager = NetworkMonitor(self._matrix, self._press_event)
        testview = TestView(self._matrix, self._press_event)
        issview = ISSView(self._matrix, self._press_event)

        views = [
            {
                "view": issview,
                "time": 700
            },
            {
                "view": networkmanager,
                "time": 700
            },
            {
                "view": testview,
                "time": 60
            },
            {
                "view": weatherview,
                "time": 358
            }
        ]

        current_view = 0
        
        self._auto_timer = None
        self._manual_timer = None

        while True:
            if self._mode == "timed":
                if self._auto_switch:
                    self._auto_switch = False
                    self._auto_timer = threading.Timer(views[current_view]["time"], self.handle_timer)
                    self._auto_timer.daemon = True
                    self._auto_timer.start()
                
                else:
                    self.cancel_timers()

                    manual_time = 300 # s.

                    self._manual_timer = threading.Timer(manual_time, self.handle_timer)
                    self._manual_timer.daemon = True
                    self._manual_timer.start()
            
            views[current_view]["view"].run()

            if self._long_press_event.is_set():
                self.handle_shutdown(poweroffview, switchview)
                current_view -= 1

            current_view = (current_view + 1) % len(views)
            
            self.clear_events()

    def cancel_timers(self):
        try:
            self._auto_timer.cancel()
            self._manual_timer.cancel()
        except AttributeError:
            pass

    def clear_events(self):
        self._long_press_event.clear()
        self._press_event.clear()

    def handle_timer(self):
        self._auto_switch = True
        self._press_event.set()

    def handle_shutdown(self, poweroffview, switchview):
        self.clear_events()
        result = poweroffview.start_shutdown()

        self.cancel_timers()

        self.clear_events()

        if result == "switch_mode":
            self._mode = switchview.show_mode(self._mode, self.MODES)
            Config.update_key("mode", self._mode)

        elif result == True:
            if Config.VIRTUAL_MODE:
                self.log("Virtual shutdown requested.")
            else:
                try:
                    import RPi.GPIO as GPIO
                    GPIO.cleanup()
                except:
                    pass
                
                os.system("systemctl poweroff -i")


    def log(self, text):
        print(f"View Handler - {text}")
