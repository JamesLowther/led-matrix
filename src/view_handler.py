import os
import threading

from views.poweroff_view import PoweroffView
from views.network_view.network_view import NetworkMonitor
from views.test_view.test_view import TestView
from views.iss_view.iss_view import ISSView
from views.weather_view.weather_view import WeatherView

class ViewHandler():
    def __init__(self, matrix, press_event, stop_event, timed_mode=False):
        self._matrix = matrix
        self._press_event = press_event
        self._stop_event = stop_event

        self._timed_mode = timed_mode
        self._auto_switch = True

    def start(self):
        poweroffview = PoweroffView(self._matrix, self._press_event)

        weatherview = WeatherView(self._matrix, self._press_event)
        networkmanager = NetworkMonitor(self._matrix, self._press_event)
        testview = TestView(self._matrix, self._press_event)
        issview = ISSView(self._matrix, self._press_event)

        views = [
            {
                "view": weatherview,
                "time": 358
            },
            {
                "view": issview,
                "time": 600
            },
            {
                "view": networkmanager,
                "time": 60
            },
            {
                "view": testview,
                "time": 60
            }
        ]

        current_view = 0
        
        auto_timer = None
        manual_timer = None

        while True:
            if self._timed_mode:
                if self._auto_switch:
                    self._auto_switch = False
                    auto_timer = threading.Timer(views[current_view]["time"], self.handle_timer)
                    auto_timer.start()
                
                else:
                    try:
                        auto_timer.cancel()
                        manual_timer.cancel()
                    except AttributeError:
                        pass

                    manual_time = 300 # s.

                    manual_timer = threading.Timer(manual_time, self.handle_timer)
                    manual_timer.start()
            
            views[current_view]["view"].run()

            if self._stop_event.is_set():
                self.handle_shutdown(poweroffview)
                current_view -= 2

            current_view = (current_view + 1) % len(views)
            self._press_event.clear()

    def handle_timer(self):
        self._auto_switch = True
        self._press_event.set()

    def handle_shutdown(self, poweroffview):
        self._stop_event.clear()
        self._press_event.clear()
        
        if poweroffview.start_shutdown():
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
            except:
                pass
            
            os.system("systemctl poweroff -i")

    
