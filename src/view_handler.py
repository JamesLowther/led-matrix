import os
import threading

from views.poweroff_view import PoweroffView
from views.network_view import NetworkMonitor
from views.test_view import TestView
from views.iss_view import ISSView
from views.weather_view import WeatherView

class ViewHandler():
    def __init__(self, matrix, press_event, stop_event, timed_mode=False):
        self._matrix = matrix
        self._press_event = press_event
        self._stop_event = stop_event

        self._timed_mode = timed_mode

    def start(self):
        poweroffview = PoweroffView(self._matrix, self._press_event)

        weatherview = WeatherView(self._matrix, self._press_event)
        networkmanager = NetworkMonitor(self._matrix, self._press_event)
        testview = TestView(self._matrix, self._press_event)
        issview = ISSView(self._matrix, self._press_event)

        views = [
            {
                "view": weatherview,
                "time": 300
            },
            {
                "view": issview,
                "time": 200
            },
            {
                "view": networkmanager,
                "time": 30
            },
            {
                "view": testview,
                "time": 30
            }
        ]


        current_view = 0

        while True:
            if self._timed_mode:
                timer = threading.Timer(views[current_view]["time"], lambda: self._press_event.set())
                timer.start()
            
            views[current_view]["view"].run()

            if self._stop_event.is_set():
                self.handle_shutdown(poweroffview)
                current_view -= 2

            current_view = (current_view + 1) % len(views)
            self._press_event.clear()

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

    