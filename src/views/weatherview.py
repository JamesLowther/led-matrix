from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from cfg import FONTS
from datetime import date, datetime

from transitions import Transitions

import time
import requests
import threading
import os

request_e = threading.Event()

new_frames = []
api_updated = False

api_error = False

class WeatherView():
    FRAME_INTERVAL = 900 # ms.
    HOLD_TIME = 2000 # ms.
    
    RADAR_LOOPS = 2

    API_INTERVAL = 60 # s.

    LOCATION_COLOR = "lightsteelblue"

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

        self._frames = []

        self._request_t = threading.Thread(name="requests", target=request_thread)
        self._request_t.daemon = True
        self._request_t.start()

        self._temperature_data = TemperatureData(self._matrix, "Calgary")

        request_e.set()

    def run(self):
        # Wait for initial frame data to be generated.
        while(not api_updated):
            time.sleep(0.1)

        self.update_frames()

        start_time = time.time()
        loop = 0

        i = 0
        while not self._press_event.is_set():
            current_time = time.time()
            if current_time - start_time >= self.API_INTERVAL:
                start_time = current_time
                request_e.set()

            if i == 0 and api_updated:
                self.update_frames()

            current_image = self._frames[i]["frame"]
            current_time = self._frames[i]["time"]

            self.draw_location(current_image)
            self.draw_time(current_image, current_time)
            self._matrix.set_image(current_image, unsafe=False)

            i = (i + 1) % len(self._frames)

            if i == 0:
                loop += 1
                msleep(self.HOLD_TIME)
            else:
                msleep(self.FRAME_INTERVAL)

            if loop == self.RADAR_LOOPS:
                loop = 0

                temperature_image = self._temperature_data.start_temperature(current_image)

                if api_updated:
                    self.update_frames()

                Transitions.vertical_transition(self._matrix, temperature_image, self._frames[0]["frame"])

    def update_frames(self):
        global api_updated
        self._frames = new_frames.copy()
        api_updated = False

    def draw_location(self, image):
        x_offset = 31 
        y_offset = 15

        w = 2
        h = 2

        d = ImageDraw.Draw(image)

        d.rectangle(
            [
                x_offset,
                y_offset,
                x_offset + w - 1,
                y_offset + h - 1
            ],
            fill=self.LOCATION_COLOR
        )

    def draw_time(self, image, time):
        x_offset = 1
        y_offset = 1

        color = (170, 170, 170)

        font_path = os.path.join(FONTS, "resolution-3x4.ttf")

        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        time_str = datetime.fromtimestamp(time).strftime("%I:%M %p")
        time_str = time_str.lstrip("0")

        text_size = d.textsize(time_str, f)

        d.text(
            (
                64 - text_size[0] - x_offset, 
                32 - text_size[1] - y_offset
            ),
            time_str,
            font=f,
            fill=color
        )

def request_thread():
    global frames

    radar_data = RadarData()

    while True:
        request_e.wait()
        radar_data.update()
        request_e.clear()

class TemperatureData():
    BG_COLOR = "red"

    def __init__(self, matrix, location):
        self._matrix = matrix
        self._location = location

    def start_temperature(self, last_frame):
        
        self.generate_temp_image()

        Transitions.vertical_transition(self._matrix, last_frame, self._temperature_image)

        msleep(1000)

        return self._temperature_image

    def generate_temp_image(self):
        self._temperature_image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)

class RadarData():
    API_FILE_URL = "https://api.rainviewer.com/public/weather-maps.json"
    
    NUMBER_PAST = 4     # Max 12.
    NUMBER_NOWCAST = 3  # Max 3.

    LATITUDE = 51.030436
    LONGITUDE = -114.065720

    ZOOM = 5
    COLOR = 2
    SMOOTH = 0
    SNOW = 1

    def __init__(self):
        self._api_file = None
        self._last_updated = 0
    
    def update(self):
        global api_updated

        self.get_api_file()

        # Check if the API data changed.
        if self._api_file["generated"] == self._last_updated:
            return

        self._last_updated = self._api_file["generated"]

        new_frames.clear()

        self.get_past_radar()
        self.get_nowcast_radar()

        api_updated = True

    def get_api_file(self):
        self._api_file = requests.get(self.API_FILE_URL).json()

    def get_past_radar(self):
        size = 512

        number_data = len(self._api_file["radar"]["past"])

        past_api_data = self._api_file["radar"]["past"][number_data - self.NUMBER_PAST:]
        
        for data in past_api_data:
            url = f"{self._api_file['host']}{data['path']}/{size}/{self.ZOOM}/{self.LATITUDE}/{self.LONGITUDE}/{self.COLOR}/{self.SMOOTH}_{self.SNOW}.png"
            radar_image = requests.get(url)

            img = Image.open(BytesIO(radar_image.content))
            converted_image = self.convert_image(img)

            new_frames.append(
                {
                    "time": data["time"],
                    "frame": converted_image
                }
            )

    def get_nowcast_radar(self):
        size = 512

        number_data = len(self._api_file["radar"]["nowcast"])

        nowcast_api_data = self._api_file["radar"]["nowcast"][number_data - self.NUMBER_NOWCAST:]
        
        for data in nowcast_api_data:
            url = f"{self._api_file['host']}{data['path']}/{size}/{self.ZOOM}/{self.LATITUDE}/{self.LONGITUDE}/{self.COLOR}/{self.SMOOTH}_{self.SNOW}.png"
            radar_image = requests.get(url)

            img = Image.open(BytesIO(radar_image.content))
            converted_image = self.convert_image(img)

            new_frames.append(
                {
                    "time": data["time"],
                    "frame": converted_image
                }
            )

    def convert_image(self, image):
        image = image.convert("RGB")
        resized = image.resize((64, 64), Image.BOX)
        cropped = resized.crop((0, 15, 64, 47))
        return cropped

def msleep(ms):
    """
    Sleep in milliseconds.
    """
    time.sleep(ms / 1000)