import urllib3
import signal
import threading
import sys

from PIL import Image

from config import Config

from button_handler import ButtonHandler

from matrix import Matrix
from view_handler import ViewHandler

urllib3.disable_warnings()

sigint_stop_event = threading.Event()
sig_matrix = None

def main():
    global sig_matrix

    Config.initialize_state()

    press_event = threading.Event()
    long_press_event = threading.Event()

    button_thread = ButtonHandler(press_event, long_press_event, sigint_stop_event)
    if Config.VIRTUAL_MODE:
        button_thread.daemon = True
    button_thread.start()

    matrix = Matrix()
    sig_matrix = matrix

    viewhandler = ViewHandler(matrix, press_event, long_press_event)
    viewhandler.start()

def signal_handler(sig, frame):
    print("Main - Sending stop event...")
    sigint_stop_event.set()

    # Hack to clear screen on termination.
    image = Image.new("RGB", sig_matrix.dimensions, color="black")     
    sig_matrix.set_image(image)
    
    print("Main - Stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    main()
