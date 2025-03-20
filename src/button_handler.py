from config import Config

try:
    import gpiozero

    gpiozero.Button.was_held = False
    Config.VIRTUAL_MODE = False
except ModuleNotFoundError:
    Config.VIRTUAL_MODE = True

import threading
import time


class ButtonHandler(threading.Thread):
    BOUNCE_TIME = 10
    HOLD_TIME = 1000

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
                    self.hold(None)
                else:
                    self.release(None)
        else:
            try:
                button = gpiozero.Button(3)
                button.hold_time = self.HOLD_TIME

                button.when_released = self.released
                button.when_held = self.held

            except RuntimeError as e:
                self.log(e)
                gpiozero.close()
                return

            self._sigint_stop_event.wait()

            self.log("Stopping...")
            gpiozero.close()
            self.log("Stopped.")

    def released(self, button):
        if Config.VIRTUAL_MODE:
            self._press_event.set()
            return

        if not button.was_held:
            self._press_event.set()

        button.was_held = False

        # time.sleep(0.05)
        # pressed = not GPIO.input(channel)

        # if pressed:
        #     if not self._button_down:
        #         self._last_press = time.time()
        #         self._button_down = True

        # else:
        #     if self._button_down:
        #         time_pressed = (time.time() - self._last_press) * 1000
        #         if time_pressed < self.HOLD_TIME:
        #             self._press_event.set()

        #         else:
        #             self._long_press_event.set()
        #             self._press_event.set()

        #         self._button_down = False

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
