try:
    import RPi.GPIO as GPIO
    VIRTUAL_BUTTON = False
except ModuleNotFoundError:
    VIRTUAL_BUTTON = True

import threading
import time

class ButtonHandler(threading.Thread):
    BOUNCE_TIME = 300
    HOLD_TIME = 3000

    def __init__(self, press_event, stop_event):
        threading.Thread.__init__(self)
        self._press_event = press_event
        self._stop_event = stop_event

        self._last_press = 0

    def run(self):
        if VIRTUAL_BUTTON:
            print("Using virtual button.")
            while True:
                input()
                self.press(3)

        else:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(3, GPIO.BOTH, callback=self.press, bouncetime=self.BOUNCE_TIME)

            except RuntimeError as e:
                self.log(e)
                GPIO.cleanup()
                return

            self._stop_event.wait()

            self.log("Stopping...")
            GPIO.cleanup()
            self.log("Stopped.")

    def press(self, channel):
        if VIRTUAL_BUTTON:
            self._press_event.set()
            return

        time.sleep(0.05)
        pressed = not GPIO.input(channel)

        if pressed:
            self._last_press = time.time()
            self._press_event.set()

        else:
            if (time.time() - self._last_press) * 1000 >= self.HOLD_TIME:
                print("LONG PRESS")

            else:
                self._press_event.set()

    def log(self, text):
        print(f"Button Handler - {text}")