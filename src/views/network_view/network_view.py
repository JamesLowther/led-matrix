from urllib import request
from PIL import Image, ImageDraw, ImageFont
from requests import Session
import json
import threading
import time
from common import msleep

from views.network_view.traffic_graph import TrafficGraph

from config import ENV_VALUES

health_data = None
traffic_interval_data = None

request_e = threading.Event()

class NetworkMonitor():
    API_INTERVAL = 5

    REFRESH_INTERVAL = 1000
    BG_COLOR = "black"

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

        self._start_time = time.time()

        self._request_t = threading.Thread(name="requests", target=request_thread)
        self._request_t.daemon = True
        self._request_t.start()

    def run(self):
        request_e.set()
        
        while health_data == None or traffic_interval_data == None:
            msleep(200)

        while not self._press_event.is_set():

            image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)     
            
            TrafficGraph.draw_graph(image, traffic_interval_data)
            TrafficGraph.draw_tx_rx(image, health_data)

            self._matrix.set_image(image)

            self.check_api_interval()

            msleep(self.REFRESH_INTERVAL)

    def check_api_interval(self):
        current_time = time.time()
        if current_time - self._start_time >= self.API_INTERVAL:
            self._start_time = current_time
            request_e.set()

def request_thread():
    global health_data
    global traffic_interval_data

    unifi = UnifiConnection()

    while True:
        request_e.wait()
        print("update")
        traffic_interval_data = unifi.update_5min_interval()[1]["data"]
        health_data = unifi.update_health()[1]["data"]
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

    def update_health(self, retry_attempts=3):
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