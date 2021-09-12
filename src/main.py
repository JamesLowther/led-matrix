import urllib3
import signal
import threading
import sys

from buttonhandler import ButtonHandler

from matrix import Matrix
from views.networkmonitor import NetworkMonitor
from views.testview import TestView
from views.issview import ISSView

urllib3.disable_warnings()

stop_event = threading.Event()

def main():
    press_event = threading.Event()
    button_thread = ButtonHandler(press_event, stop_event)
    button_thread.start()

    matrix = Matrix()

    networkmanager = NetworkMonitor(matrix, press_event)
    testview = TestView(matrix, press_event)
    issview = ISSView(matrix, press_event)

    views = [
        networkmanager,
        testview,
        issview
    ]

    current_view = 0

    while True:
        views[current_view].run()
        current_view = (current_view + 1) % len(views)
        press_event.clear()

def signal_handler(sig, frame):
    print("Main - Sending stop event...")
    stop_event.set()
    print("Main - Stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main()