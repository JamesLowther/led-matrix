from os import confstr
import urllib3
import signal
import threading
import sys

from config import Config

from button_handler import ButtonHandler

from matrix import Matrix
from view_handler import ViewHandler

urllib3.disable_warnings()

sigint_stop_event = threading.Event()

def main():
    Config.initialize_state()

    press_event = threading.Event()
    long_press_event = threading.Event()

    button_thread = ButtonHandler(press_event, long_press_event, sigint_stop_event)
    button_thread.start()

    matrix = Matrix()

    viewhandler = ViewHandler(matrix, press_event, long_press_event)
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
