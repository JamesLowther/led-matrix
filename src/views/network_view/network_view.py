from urllib import request
from PIL import Image, ImageDraw, ImageFont
from requests import Session
import json
import threading
import time
from time import sleep

from config import ENV_VALUES

request_e = threading.Event()

class NetworkMonitor():
    REFRESH_INTERVAL = 1

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

        self._request_t = threading.Thread(name="requests", target=request_thread)
        self._request_t.daemon = True
        self._request_t.start()

    def run(self):
        request_e.set()

        while not self._press_event.is_set():            
            

            sleep(self.REFRESH_INTERVAL)

def request_thread():
    unifi = UnifiConnection()

    while True:
        request_e.wait()
        data = unifi.update_5min_interval()
        print(data)
        request_e.clear()

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

    def update_5min_interval(self, retry_attempts=3):
        minutes_interval = 35

        attrs = [
            "time",
            "wan-tx_bytes",
            "wan-rx_bytes"
        ]

        end = time.time() * 1000
        start = end - (minutes_interval * 60 * 1000)

        success = False
        for i in range(retry_attempts):
            response = self._session.post(
                f"{self.ENDPOINT}/api/s/{self.SITE}/stat/report/5minutes.site",
                json={
                    "start": start,
                    "end": end,
                    "attrs": attrs
                },
                verify=False
            )

            data = json.loads(response.text)

            if data["meta"]["rc"] == "ok":
                success = True
                break

            # Attempt to login if the query failed.
            self.login()         

        return (success, data)

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