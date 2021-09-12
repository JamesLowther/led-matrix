try:
    import RPi.GPIO as GPIO
    VIRTUAL_BUTTON = False
except ModuleNotFoundError:
    VIRTUAL_BUTTON = True

import time

def button_handler(press_event):
    if VIRTUAL_BUTTON:
        while True:
            input("enter")

    else:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        while True:
            GPIO.wait_for_edge(3, GPIO.FALLING)
            print("press")