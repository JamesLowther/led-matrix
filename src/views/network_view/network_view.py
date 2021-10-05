from urllib import request
from PIL import Image, ImageDraw, ImageFont
from requests import Session
import json
from time import sleep

from config import ENV_VALUES

class NetworkMonitor():
    REFRESH_INTERVAL = 1

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

    def run(self):
        unifi = UnifiConnection()

        while not self._press_event.is_set():
            _, data = unifi.update()

            # print(data)
            
            image = Image.new("RGB", self._matrix.dimensions, color="black")
            f = ImageFont.truetype("./src/assets/fonts/6px-Normal.ttf", 8)
            d = ImageDraw.Draw(image)

            text = f"{data['data'][0]['num_user']} clients"

            text_size = d.textsize(text, f)

            d.text(
                (
                    (self._matrix.dimensions[0] // 2) - text_size[0] // 2, 
                    (self._matrix.dimensions[1] // 2) - text_size[1] // 2
                ),
                text,
                font=f,
                fill=(255, 255, 255)
            )

            self._matrix.set_image(image)

            sleep(self.REFRESH_INTERVAL)

class UnifiConnection():
    ENDPOINT = "https://192.168.1.5:8443"
    SITE = "default"

    def __init__(self):
        self._session = Session()

        self.login()

    def login(self):
        """
        Login to the Unifi controller.
        Sets the cookie for the session.
        """
        self._session.post(
            f"{self.ENDPOINT}/api/login",
            json={
                "username": ENV_VALUES["UNIFI_USERNAME"],
                "password": ENV_VALUES["UNIFI_PASSWORD"]
            },
            verify=False
        )

    def logout(self):
        """
        Logout of the Unifi controller.
        Deletes the cookie for the session. 
        """
        self._session.post(
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
            response = self._session.get(
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