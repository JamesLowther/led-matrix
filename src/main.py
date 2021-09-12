from PIL import Image, ImageDraw
import urllib3

from buttonhandler import button_handler

import threading

from matrix import Matrix
from views.networkmonitor import NetworkMonitor
from views.testview import TestView
from views.issview import ISSView
import os

urllib3.disable_warnings()

def main():

    press_event = threading.Event()
    button_thread = threading.Thread(target=button_handler, args=(press_event,))
    button_thread.start()


    matrix = Matrix()

    # networkmanager = NetworkMonitor(matrix)
    # networkmanager.run()

    # testview = TestView(matrix)
    # testview.run()

    issview = ISSView(matrix)
    issview.run()

if __name__ == "__main__":
    main()