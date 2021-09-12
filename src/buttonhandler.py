try:
    import RPi.GPIO as GPIO
    VIRTUAL_BUTTON = False
except ModuleNotFoundError:
    VIRTUAL_BUTTON = True

import time

def button_handler(press_event, stop_event):
    if VIRTUAL_BUTTON:
        while True:
            press(3)

    else:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(3, GPIO.FALLING, callback=press)

        stop_event.wait()

        GPIO.cleanup()
        print("Stopped button handler.")

def press(channel):
    print(channel)