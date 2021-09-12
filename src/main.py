from PIL import Image, ImageDraw
import urllib3

from matrix import Matrix
from views.networkmonitor import NetworkMonitor
from views.testview import TestView
from views.issview import ISSView
import os

urllib3.disable_warnings()

def main():
    matrix = Matrix()

    # networkmanager = NetworkMonitor(matrix)
    # networkmanager.run()

    # testview = TestView(matrix)
    # testview.run()

    issview = ISSView(matrix)
    issview.run()

    input()

if __name__ == "__main__":
    main()