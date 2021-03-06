from config import Config

try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
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
                    self.press(3, virtual_press_type="long")
                else:
                    self.press(3, virtual_press_type="short")
        else:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(3, GPIO.BOTH, callback=self.press, bouncetime=self.BOUNCE_TIME)

            except RuntimeError as e:
                self.log(e)
                GPIO.cleanup()
                return

            self._sigint_stop_event.wait()

            self.log("Stopping...")
            GPIO.cleanup()
            self.log("Stopped.")

    def press(self, channel, virtual_press_type=None):
        if Config.VIRTUAL_MODE:
            if virtual_press_type == "short":
                self._press_event.set()
                return
            elif virtual_press_type == "long":
                self._long_press_event.set()
                self._press_event.set()
                return

        time.sleep(0.05)
        pressed = not GPIO.input(channel)

        if pressed:
            if not self._button_down:
                self._last_press = time.time()
                self._button_down = True

        else:
            if self._button_down:
                time_pressed = (time.time() - self._last_press) * 1000
                if time_pressed < self.HOLD_TIME:
                    self._press_event.set()

                else:
                    self._long_press_event.set()
                    self._press_event.set()

                self._button_down = False

    def log(self, text):
        print(f"Button Handler - {text}")