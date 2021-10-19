from urllib import request
from PIL import Image, ImageDraw, ImageFont
from requests import Session
import requests
import json
import threading
import time
from common import msleep
import os
import subprocess

from views.network_view.traffic_graph import TrafficGraph

from config import Config

initial_api_updated = False
api_error = False

pihole_data = None
health_data = None
ping_data = None
traffic_interval_data = None

request_e = threading.Event()

class NetworkMonitor():
    API_INTERVAL = 5 # s.

    REFRESH_INTERVAL = 800 # ms.
    BG_COLOR = "black"

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

        self._start_time = time.time()

        self._request_t = threading.Thread(name="requests", target=request_thread)
        self._request_t.daemon = True
        self._request_t.start()

    def run(self):
        global initial_api_updated

        initial_api_updated = False

        request_e.set()
        
        while not initial_api_updated:
            msleep(200)

        while not self._press_event.is_set():

            image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)     
            
            self.draw_time(image)
            self.draw_clients(image)
            self.draw_pihole(image)
            self.draw_ping(image)

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

    def draw_time(self, image):
        """
        Draws the current time.
        """
        
        x_offset = 2
        y_offset = 1

        color = "thistle"

        font_path = os.path.join(Config.FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        time_str = time.strftime("%I:%M %p")

        d.text(
            (x_offset, y_offset),
            time_str,
            font=f,
            fill=color
        )

    def draw_clients(self, image):
        x_offset = 2
        y_offset = 10

        color = "rosybrown"

        font_path = os.path.join(Config.FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        num_clients = health_data[1]["num_sta"]

        client_str = f"{num_clients} clnts"

        d.text(
            (x_offset, y_offset),
            client_str,
            font=f,
            fill=color
        )

    def draw_ping(self, image):
        x_offset = 1
        y_offset = 10

        color = "rosybrown"

        font_path = os.path.join(Config.FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        ms_str = str(round(ping_data, 1)) + " ms"
        ms_size = d.textsize(ms_str, f)

        d.text(
            (
                64 - ms_size[0] - x_offset,
                y_offset
            ),
            ms_str,
            font=f,
            fill=color
        )

    def draw_pihole(self, image):
        x_offset = 1
        y_offset = 1

        x_spacing = 2

        icon_size = 7

        icon = None
        if pihole_data["status"] == "enabled":
            icon = self.get_icon("pihole", icon_size)
        else:
            icon = self.get_icon("pihole-off", icon_size)

        color = "lightcoral"

        font_path = os.path.join(Config.FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(image)

        percent = round(pihole_data["ads_percentage_today"], 1)
        percent_str = f"{percent}%"
        percent_size = d.textsize(percent_str, f)

        image.paste(
            icon,
            (
                64 - percent_size[0] - icon_size - x_offset - x_spacing,
                y_offset
            )
        )

        d.text(
            (
                64 - percent_size[0] - x_offset, 
                y_offset + ((icon_size / 2) - (percent_size[1] / 2))
            ),
            percent_str,
            font=f,
            fill=color
        )

    def get_icon(self, code, size):
        path = os.path.join(Config.SRC_BASE, "assets", "networkview", f"{code}.png")
        image = Image.open(path)

        resized = image.resize((size, size), Image.BOX)

        return resized

def request_thread():
    global initial_api_updated
    global pihole_data
    global health_data
    global traffic_interval_data
    global ping_data

    unifi = UnifiConnection()
    pihole = PiHoleConnection()
    ping = PingConnection()

    while True:
        request_e.wait()
        ping_data = ping.update()
        pihole_data = pihole.update()
        traffic_interval_data = unifi.update_5min_interval()[1]["data"]
        health_data = unifi.update_health()[1]["data"]
        request_e.clear()

        initial_api_updated = True

class PingConnection():
    ENDPOINT = "8.8.8.8"

    def update(self):
        resp = str(subprocess.check_output("ping -c 1 " + self.ENDPOINT, shell=True))
        last = resp.rindex("/")
        s_last = resp.rindex("/", 0, last)

        return float(resp[s_last + 1:last])

class PiHoleConnection():
    ENDPOINT = "http://192.168.1.5/admin/api.php"

    def update(self):

        data = requests.get(
            self.ENDPOINT
        ).json()

        return data

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
                "username": Config.ENV_VALUES["UNIFI_USERNAME"],
                "password": Config.ENV_VALUES["UNIFI_PASSWORD"]
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
        minutes_interval = 65

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