from PIL import Image, ImageDraw
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
    # button_thread = threading.Thread(target=button_handler, args=(press_event, stop_event))
    button_thread = ButtonHandler(press_event, stop_event)
    button_thread.start()

    press_event.wait()

    matrix = Matrix()

    # networkmanager = NetworkMonitor(matrix)
    # networkmanager.run()

    # testview = TestView(matrix)
    # testview.run()

    issview = ISSView(matrix)
    issview.run()

def signal_handler(sig, frame):
    print("Stopping...")
    stop_event.set()

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main()