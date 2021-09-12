try:
    import RPi.GPIO as GPIO
    VIRTUAL_BUTTON = False
except ModuleNotFoundError:
    VIRTUAL_BUTTON = True

import time
import threading

class ButtonHandler(threading.Thread):
    PRESS_TIMEOUT = 1500

    def __init__(self, press_event, stop_event):
        threading.Thread.__init__(self)
        self.press_event = press_event
        self.stop_event = stop_event

    def run(self):
        if VIRTUAL_BUTTON:
            print("Using virtual button.")
            while True:
                input()
                self.press(3)

        else:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(3, GPIO.FALLING, callback=self.press)

            self.stop_event.wait()

            GPIO.cleanup()
            print("Stopped button handler.")

    def press(self, channel):
        print("\npress\n")
        self.press_event.set()
        time.sleep(self.PRESS_TIMEOUT / 1000)