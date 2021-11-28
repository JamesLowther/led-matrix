import os
import threading

from config import Config

from views.poweroff_view import PoweroffView
from views.switch_view import SwitchView
from views.network_view.network_view import NetworkMonitor
from views.test_view.test_view import TestView
from views.iss_view.iss_view import ISSView
from views.video_view.video_view import VideoView
from views.weather_view.weather_view import WeatherView

class ViewHandler:
    MODES = [
        "timed",
        "manual",
    ]

    START_VIEW = 5

    def __init__(self, matrix, press_event, long_press_event):
        self._matrix = matrix
        self._press_event = press_event
        self._long_press_event = long_press_event

        self._mode = Config.read_key("mode")
        self._auto_switch = True

        self._current_view = self.START_VIEW

    def start(self):
        poweroff_view = PoweroffView(self._matrix, self._press_event, self._long_press_event)
        switch_view = SwitchView(self._matrix, self._press_event, self._long_press_event)

        # Real-time views.
        weather_view = WeatherView(self._matrix, self._press_event)
        network_view = NetworkMonitor(self._matrix, self._press_event)
        test_view = TestView(self._matrix, self._press_event)
        iss_view = ISSView(self._matrix, self._press_event)

        # Video views.
        fireplace_view = VideoView(self._matrix, self._press_event, "fireplace")
        jeremy_view = VideoView(self._matrix, self._press_event, "jeremy")

        views = [
            {
                "view": iss_view,
                "time": 700
            },
            {
                "view": network_view,
                "time": 700
            },
            {
                "view": weather_view,
                "time": 410
            },
            {
                "view": test_view,
                "time": 120
            },
            {
                "view": fireplace_view,
                "time": 200
            },
            {
                "view": jeremy_view,
                "time": 200
            }
        ]

        if self._mode == "manual":
            self._current_view = Config.read_key("view")
            
        self._auto_timer = None
        self._manual_timer = None

        while True:
            if self._mode == "timed":
                if self._auto_switch:
                    self._auto_switch = False
                    self._auto_timer = threading.Timer(views[self._current_view]["time"], self.handle_timer)
                    self._auto_timer.daemon = True
                    self._auto_timer.start()
                
                else:
                    self.cancel_timers()

                    manual_time = 300 # s.

                    self._manual_timer = threading.Timer(manual_time, self.handle_timer)
                    self._manual_timer.daemon = True
                    self._manual_timer.start()
            
            views[self._current_view]["view"].run()

            if self._long_press_event.is_set():
                self.handle_shutdown(poweroff_view, switch_view)
                self._current_view -= 1

            self._current_view = (self._current_view + 1) % len(views)
            
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

    def save_view(self):
        if self._mode == "manual":
            Config.update_key("view", self._current_view)

    def handle_shutdown(self, poweroff_view, switch_view):
        self.clear_events()
        result = poweroff_view.start_shutdown()

        self.cancel_timers()

        self.clear_events()

        if result == "switch_mode":
            self._mode = switch_view.show_mode(self._mode, self.MODES)
            Config.update_key("mode", self._mode)

        elif result == True:
            self.save_view()
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
