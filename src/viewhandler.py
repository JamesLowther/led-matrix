import os
import threading

from views.poweroffview import PoweroffView
from views.networkmonitor import NetworkMonitor
from views.testview import TestView
from views.issview import ISSView
from views.weatherview import WeatherView

class ViewHandler():
    def __init__(self, matrix, press_event, stop_event, timed_mode=False):
        self._matrix = matrix
        self._press_event = press_event
        self._stop_event = stop_event

        self._timed_mode = timed_mode
        self._view_time = 300 # s.

    def start(self):
        poweroffview = PoweroffView(self._matrix, self._press_event)

        weatherview = WeatherView(self._matrix, self._press_event)
        networkmanager = NetworkMonitor(self._matrix, self._press_event)
        testview = TestView(self._matrix, self._press_event)
        issview = ISSView(self._matrix, self._press_event)

        views = [
            weatherview,
            issview,
            # networkmanager,
            # testview
        ]


        current_view = 0

        while True:
            if self._timed_mode:
                timer = threading.Timer(self._view_time, lambda: self._press_event.set())
                timer.start()
            
            views[current_view].run()

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

    