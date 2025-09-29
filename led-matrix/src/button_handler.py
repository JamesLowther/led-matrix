from config import Config

try:
    from gpiozero import Button

    Button.was_held = False
    Config.VIRTUAL_MODE = False
except ModuleNotFoundError:
    Config.VIRTUAL_MODE = True

import threading
import time


class ButtonHandler(threading.Thread):
    BOUNCE_TIME = 0.01
    HOLD_TIME = 1

    def __init__(self, press_event, long_press_event, sigint_stop_event):
        threading.Thread.__init__(self)
        self._press_event = press_event
        self._long_press_event = long_press_event
        self._sigint_stop_event = sigint_stop_event

        self._last_press = 0
        self._button_down = False

        if Config.VIRTUAL_MODE_OVERRIDE:
            Config.VIRTUAL_MODE = True

    def run(self):
        if Config.VIRTUAL_MODE:
            self.log("Virtual button enabled.")
            while True:
                k = input()
                if k == "l":
                    self.held(None)
                else:
                    self.released(None)
        else:
            try:
                button = Button(3, bounce_time=self.BOUNCE_TIME)
                button.hold_time = self.HOLD_TIME

                button.when_released = self.released
                button.when_held = self.held

            except RuntimeError as e:
                self.log(e)
                button.close()
                return

            self._sigint_stop_event.wait()

            self.log("Stopping...")
            button.close()
            self.log("Stopped.")

    def released(self, button):
        if Config.VIRTUAL_MODE:
            self._press_event.set()
            return

        if not button.was_held:
            self._press_event.set()

        button.was_held = False

    def held(self, button):
        if Config.VIRTUAL_MODE:
            self._long_press_event.set()
            self._press_event.set()
            return

        button.was_held = True

        self._long_press_event.set()
        self._press_event.set()

    def log(self, text):
        print(f"Button Handler - {text}")
