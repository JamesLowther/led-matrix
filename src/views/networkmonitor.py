from PIL import Image, ImageDraw
from requests import Session
from dotenv import dotenv_values

class NetworkMonitor():
    def __init__(self, matrix):
        self.matrix = matrix

    def run(self):
        image = Image.new("RGB", self.matrix.dimensions, color="green")
        d = ImageDraw.Draw(image)
        d.text((0, 0), "Hello,", fill=(255, 255, 255))
        d.text((0, 10), "world!", fill=(255, 255, 255))

        self.matrix.set_image(image)

        unifi = UnifiConnection()

class UnifiConnection():
    def __init__(self):
        self.__config = dotenv_values()
        self.__session = Session()

        self.connect()

    def connect(self):
        print(self.__config)

    def update(self):
        pass