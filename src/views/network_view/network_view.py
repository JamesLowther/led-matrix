from urllib import request
from PIL import Image, ImageDraw, ImageFont
from requests import Session, api
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

class NetworkMonitor:
    API_INTERVAL = 10 # s.

    REFRESH_INTERVAL = 10000 # ms.
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
        global api_error

        initial_api_updated = False

        request_e.set()

        while not initial_api_updated:
            msleep(200)

        while not self._press_event.is_set():

            image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)

            if api_error:
                self.draw_error(image)

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

    def draw_error(self, image):
        x_offset = 33
        y_offset = 15

        size_1 = 2
        size_2 = 4

        color = "red"

        d = ImageDraw.Draw(image)

        d.rectangle(
            [
                x_offset,
                y_offset,
                x_offset + size_1 - 1,
                y_offset + size_1 - 1
            ],
            fill=color
        )

        d.rectangle(
            [
                x_offset,
                y_offset - 5,
                x_offset + size_1 - 1,
                y_offset + - 5 + size_2 - 1
            ],
            fill=color
        )

    def draw_time(self, image):
        """
        Draws the current time.
        """

        x_offset = 2
        y_offset = 1

        color = "lightpink"

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
        y_offset = 9

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
        y_offset = 9

        color = "rosybrown"

        font_path = os.path.join(Config.FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        ms_str = str(round(ping_data, 1)) + " ms"
        ms_size = d.textsize(ms_str, f)

        d.text(
            (
                self._matrix.dimensions[0] - ms_size[0] - x_offset,
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

        if len(percent_str) <= 4:
            x_spacing += 3

        elif len(percent_str) >= 6:
            x_spacing += -2

        image.paste(
            icon,
            (
                self._matrix.dimensions[0] - percent_size[0] - icon_size - x_offset - x_spacing,
                y_offset
            )
        )

        d.text(
            (
                self._matrix.dimensions[0] - percent_size[0] - x_offset,
                y_offset + ((icon_size / 2) - (percent_size[1] / 2))
            ),
            percent_str,
            font=f,
            fill=color
        )

    def get_icon(self, code, size):
        path = os.path.join(Config.SRC_BASE, "assets", "network_view", f"{code}.png")
        image = Image.open(path)

        resized = image.resize((size, size), Image.BOX)

        return resized

def request_thread():
    global api_error

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
        ping_return = ping.update()
        pihole_return = pihole.update()
        traffic_interval_return = unifi.update_5min_interval()
        health_return = unifi.update_health()

        if False in [ping_return, pihole_return, traffic_interval_return, health_return]:
            api_error = True
        else:
            api_error = False

        ping_data = ping_return if ping_return else 0

        if pihole_return:
            pihole_data = pihole_return
        else:
            pihole_data = {
                "ads_percentage_today": 0.0,
                "status": "disabled"
            }

        if traffic_interval_return:
            traffic_interval_data = traffic_interval_return["data"]
        else:
            traffic_interval_data = []

        if health_return:
            health_data = health_return["data"]
        else:
            health_data = [
                None,
                {
                    "num_sta": 0,
                    "tx_bytes-r": 0,
                    "rx_bytes-r": 0
                }
            ]

        request_e.clear()

        initial_api_updated = True

class PingConnection:
    ENDPOINT = "8.8.8.8"

    def update(self):
        resp = None
        try:
            resp = str(subprocess.check_output("ping -c 1 " + self.ENDPOINT, shell=True))
        except subprocess.CalledProcessError:
            return False

        last = resp.rindex("/")
        s_last = resp.rindex("/", 0, last)

        return float(resp[s_last + 1:last])

class PiHoleConnection:
    ENDPOINT = "http://192.168.1.2/admin/api.php"

    def update(self):
        try:
            data = requests.get(
                self.ENDPOINT
            ).json()

            return data
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError):
            return False

class UnifiConnection:
    ENDPOINT = "https://192.168.1.2:8443"
    SITE = "default"

    def __init__(self):
        self._session = Session()

        self.login()

    def login(self):
        """
        Login to the Unifi controller.
        Sets the cookie for the session.
        """

        try:
            self._session.post(
                f"{self.ENDPOINT}/api/login",
                json={
                    "username": Config.ENV_VALUES["UNIFI_USERNAME"],
                    "password": Config.ENV_VALUES["UNIFI_PASSWORD"]
                },
                verify=False
            )
        except requests.exceptions.RequestException:
            return

        except KeyError:
            return

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

        data = None
        for _ in range(retry_attempts):
            try:
                data = self._session.post(
                    f"{self.ENDPOINT}/api/s/{self.SITE}/stat/report/5minutes.site",
                    json={
                        "start": start,
                        "end": end,
                        "attrs": attrs
                    },
                    verify=False
                ).json()

            except (requests.exceptions.RequestException, json.decoder.JSONDecodeError):
                continue

            if data["meta"]["rc"] == "ok":
                return data

            # Attempt to login if the query failed.
            self.login()

        return False

    def update_health(self, retry_attempts=3):
        """
        Queries the Unifi controller for network information.
        Returns the success status and the JSON data.
        """
        data = None
        for _ in range(retry_attempts):
            try:
                data = self._session.get(
                    f"{self.ENDPOINT}/api/s/{self.SITE}/stat/health",
                    verify=False
                ).json()
            except (requests.exceptions.RequestException, json.decoder.JSONDecodeError):
                continue

            if data["meta"]["rc"] == "ok" and data["data"][1]["status"] == "ok":
                return data

            # Attempt to login if the query failed.
            self.login()

        return False
