from PIL import Image, ImageDraw
import urllib3

from matrix import Matrix
from views.networkmonitor import NetworkMonitor

urllib3.disable_warnings()

def main():
    matrix = Matrix()

    networkmanager = NetworkMonitor(matrix)
    networkmanager.run()


    input()

if __name__ == "__main__":
    main()