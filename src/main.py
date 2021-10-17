import urllib3
import signal
import threading
import sys

from button_handler import ButtonHandler

from matrix import Matrix
from view_handler import ViewHandler

urllib3.disable_warnings()

sigint_stop_event = threading.Event()

def main():
    press_event = threading.Event()
    stop_event = threading.Event()

    button_thread = ButtonHandler(press_event, stop_event, sigint_stop_event)
    button_thread.start()

    matrix = Matrix()

    viewhandler = ViewHandler(matrix, press_event, stop_event, timed_mode=False)
    viewhandler.start()

def signal_handler(sig, frame):
    print("Main - Sending stop event...")
    sigint_stop_event.set()
    print("Main - Stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    main()
