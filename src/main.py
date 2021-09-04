#!/usr/bin/env python


from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw
from views.networkmonitor import NetworkMonitor

from matrix import Matrix

def main():
    matrix = Matrix()

    networkmanager = NetworkMonitor(matrix)
    networkmanager.run()


    input()

if __name__ == "__main__":
    main()