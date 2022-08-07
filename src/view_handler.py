import os
import threading
from random import randint, choice

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

    START_VIEW = 0      # Index of view to start with.
    MANUAL_TIME = 300   # How long to hold view after manual press.

    def __init__(self, matrix, press_event, long_press_event):
        self._matrix = matrix
        self._press_event = press_event
        self._long_press_event = long_press_event

        self._auto_switch = True

        self.init_views()
        self.init_mode()

    def init_views(self):
        self._poweroff_view = PoweroffView(self._matrix, self._press_event, self._long_press_event)
        self._switch_view = SwitchView(self._matrix, self._press_event, self._long_press_event)

        self._views = [
            {
                "view": ISSView(self._matrix, self._press_event),
                "time": 700,
                "auto": True
            },
            {
                "view": NetworkMonitor(self._matrix, self._press_event),
                "time": 700,
                "auto": True
            },
            {
                "view": WeatherView(self._matrix, self._press_event),
                "time": 410,
                "auto": True
            },
            {
                "view": TestView(self._matrix, self._press_event),
                "time": 120,
                "auto": True
            },
            {
                "view": VideoView(self._matrix, self._press_event, "fireplace"),
                "time": 300,
                "auto": True
            },
            {
                "random": [
                    {
                        "view": VideoView(self._matrix, self._press_event, "balls", loop=False),
                        "time": 120,
                        "auto": True
                    },
                    {
                        "view": VideoView(self._matrix, self._press_event, "pillows", loop=False),
                        "time": 120,
                        "auto": True
                    },
                    {
                        "view": VideoView(self._matrix, self._press_event, "obi", loop=False),
                        "time": 120,
                        "auto": True
                    }
                ],
                "probability": 0.1
            },
            {
                "view": VideoView(self._matrix, self._press_event, "jeremy"),
                "time": 120,
                "auto": False
            },
        ]

    def init_mode(self):
        # Pull mode from config.
        self._mode = Config.read_key("mode")
        if self._mode not in self.MODES:
            self._mode = "timed"
            Config.update_key("mode", self._mode)

        # Set view from config.
        if self._mode == "manual":
            self._current_view = Config.read_key("view")
        else:
            self._current_view = self.START_VIEW

        # Check view index is within bounds.
        if self._current_view >= len(self._views):
            self._current_view = self.START_VIEW
            Config.update_key("view", self._current_view)

    def start(self):
        self._auto_timer = None
        self._manual_timer = None

        skip = False

        while True:
            self._view = self.get_next_view()

            if self._mode == "timed":
                # View was changed automatically. Start the auto timer.
                if self._auto_switch:
                    if not self._view["auto"]:
                        skip = True

                    else:
                        self._auto_switch = False
                        self.start_auto_timer()

                # View was changed manually. Start the manual timer.
                else:
                    self.start_manual_timer()

            # Start the view.
            if not skip:
                self.save_view()
                result = self._view["view"].run()

                # View quit on its own. Considered an auto switch.
                if result:
                    self._auto_switch = True

            skip = False

            # Start shutdown view if long press detected.
            if self._long_press_event.is_set():
                self.handle_shutdown()
                self._current_view -= 1

            # Increment the view.
            self.increment_view()

            # Reset state.
            self.cancel_timers()
            self.clear_events()

    def get_next_view(self):
        view = self._views[self._current_view]

        while "random" in view.keys():
            r = randint(1,100)
            if not self._auto_switch or r <= view["probability"] * 100:
                return choice(view["random"])

            self.increment_view()
            view = self._views[self._current_view]

        return view

    def increment_view(self):
        self._current_view = (self._current_view + 1) % len(self._views)

    def start_auto_timer(self):
        self._auto_timer = threading.Timer(self._view["time"], self.handle_timer)
        self._auto_timer.daemon = True
        self._auto_timer.start()

    def start_manual_timer(self):
        self._manual_timer = threading.Timer(self.MANUAL_TIME, self.handle_timer)
        self._manual_timer.daemon = True
        self._manual_timer.start()

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

    def handle_shutdown(self):
        self.clear_events()
        result = self._poweroff_view.start_shutdown()

        self.cancel_timers()
        self.clear_events()

        # Go into switch mode view.
        if result == "switch_mode":
            self._mode = self._switch_view.show_mode(self._mode, self.MODES)
            Config.update_key("mode", self._mode)

        # Start the shutdown process.
        elif result == True:
            if Config.VIRTUAL_MODE:
                self.log("Virtual shutdown requested.")
            else:
                try:
                    import RPi.GPIO as GPIO
                    GPIO.cleanup()
                except:
                    pass

                os.setuid(0)
                os.setgid(0)
                # print(os.getuid())
                # print(os.getgid())
                os.system("systemctl poweroff -i")

    def log(self, text):
        print(f"View Handler - {text}")
