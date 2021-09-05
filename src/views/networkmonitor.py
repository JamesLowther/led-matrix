from urllib import request
from PIL import Image, ImageDraw, ImageFont
from requests import Session
from dotenv import dotenv_values
import json, os
from time import sleep

class NetworkMonitor():
    REFRESH_INTERVAL = 1

    def __init__(self, matrix):
        self.matrix = matrix

    def run(self):
        unifi = UnifiConnection()

        while True:
            _, data = unifi.update()

            # print(data)
            
            image = Image.new("RGB", self.matrix.dimensions, color="black")
            f = ImageFont.truetype("NotoSansMono-Regular.ttf", 8)
            # f = ImageFont.truetype("./src/assets/font/FFFFORWA.TTF", 8)
            d = ImageDraw.Draw(image)
            d.fontmode = 1
            d.text(
                (0, 0),
                f"{str(data['data'][0]['num_user'])} clients",
                font=f,
                fill=(255, 255, 255)
            )

            self.matrix.set_image(image)

            sleep(self.REFRESH_INTERVAL)

class UnifiConnection():
    ENDPOINT = "https://192.168.1.5:8443"
    SITE = "default"

    def __init__(self):
        self.__config = dotenv_values()
        self.__session = Session()

        self.login()

    def login(self):
        """
        Login to the Unifi controller.
        Sets the cookie for the session.
        """
        self.__session.post(
            f"{self.ENDPOINT}/api/login",
            json={
                "username": self.__config["UNIFI_USERNAME"],
                "password": self.__config["UNIFI_PASSWORD"]
            },
            verify=False
        )

    def logout(self):
        """
        Logout of the Unifi controller.
        Deletes the cookie for the session. 
        """
        self.__session.post(
            f"{self.ENDPOINT}/api/logout",
            verify=False
        )

    def update(self, retry_attempts=3):
        """
        Queries the Unifi controller for network information.
        Returns the success status and the JSON data.
        """
        success = False
        for i in range(retry_attempts):
            response = self.__session.get(
                f"{self.ENDPOINT}/api/s/{self.SITE}/stat/health",
                verify=False
            )

            data = json.loads(response.text)

            if data["meta"]["rc"] == "ok":
                success = True
                break

            # Attempt to login if the query failed.
            self.login()                

        return (success, data)