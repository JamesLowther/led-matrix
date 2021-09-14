import urllib3
import signal
import threading
import sys
import os

from buttonhandler import ButtonHandler

from matrix import Matrix
from views.poweroffview import PoweroffView
from views.networkmonitor import NetworkMonitor
from views.testview import TestView
from views.issview import ISSView

urllib3.disable_warnings()

sigint_stop_event = threading.Event()
press_event = threading.Event()
stop_event = threading.Event()

def main():
    button_thread = ButtonHandler(press_event, stop_event, sigint_stop_event)
    button_thread.start()

    matrix = Matrix()

    poweroffview = PoweroffView(matrix, press_event)

    networkmanager = NetworkMonitor(matrix, press_event)
    testview = TestView(matrix, press_event)
    issview = ISSView(matrix, press_event)

    views = [
        issview,
        networkmanager,
        testview
    ]

    current_view = 0

    while True:
        views[current_view].run()
        
        if stop_event.is_set():
            handle_shutdown(poweroffview)
            current_view -= 2

        current_view = (current_view + 1) % len(views)
        press_event.clear()

def handle_shutdown(poweroffview):
    stop_event.clear()
    press_event.clear()
    
    if poweroffview.start_shutdown():
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass
        
        os.system("systemctl poweroff -i")

def signal_handler(sig, frame):
    print("Main - Sending stop event...")
    sigint_stop_event.set()
    print("Main - Stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main()
