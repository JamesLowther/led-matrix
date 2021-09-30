from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from PIL.ImageChops import offset
from cfg import FONTS, ENV_VALUES, SRC_BASE
from datetime import datetime

from transitions import Transitions

import time
import requests
import threading
import os

request_e = threading.Event()

new_frames = []
radar_api_updated = False

weather_data = {}
weather_api_updated = False

api_error = False

LOCATIONS = [
    {
        "name": "Calgary",
        "lat": 51.030436,
        "lon": -114.065720
    },
    {
        "name": "Seattle",
        "lat": 47.6062,
        "lon": -122.3321
    },
    {
        "name": "Tokyo",
        "lat": 35.6762,
        "lon": 139.6503
    }
]

class WeatherView():
    FRAME_INTERVAL = 900 # ms.
    HOLD_TIME = 2000 # ms.
    
    FORECAST_INTERVAL = 6000 # ms.

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

        self._location_tempurature_data = []
        for location in LOCATIONS:
            self._location_tempurature_data.append(
                TemperatureData(self._matrix, location["name"])
            )

        request_e.set()

    def run(self):
        # Wait for initial frame data to be generated.
        while(not radar_api_updated):
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

            # Check if api has updated radar images.
            if i == 0 and radar_api_updated:
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

                prev_image = current_image
                for i, location in enumerate(self._location_tempurature_data):
                    next_image = location.generate_temperature_image()
                    if i == 0:
                        Transitions.vertical_transition(self._matrix, prev_image, next_image)

                    else:
                        Transitions.horizontal_transition(self._matrix, prev_image, next_image)

                    msleep(self.FORECAST_INTERVAL)
                    prev_image = next_image

                if radar_api_updated:
                    self.update_frames()

                Transitions.vertical_transition(self._matrix, prev_image, self._frames[0]["frame"])

    def update_frames(self):
        global radar_api_updated
        self._frames = new_frames.copy()
        radar_api_updated = False

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

class TemperatureData():
    BG_COLOR = "black"
    INTERVAL = 10000

    def __init__(self, matrix, location):
        self._matrix = matrix
        self._location = location

    def generate_temperature_image(self):
        self._temperature_image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)

        self.draw_location_text()
        self.draw_current_temp()
        self.draw_forecast()

        return self._temperature_image

    def draw_location_text(self):
        font_path = os.path.join(FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(self._temperature_image)

        x_offset = 2
        y_offset = 2

        color = (170, 170, 170)

        d.text(
            (x_offset, y_offset),
            self._location,
            font=f,
            fill=color
        )

    def draw_current_temp(self):
        font_path = os.path.join(FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(self._temperature_image)

        x_offset = 2
        y_offset = 3

        radius = 1

        color = (170, 170, 170)

        data = weather_data[self._location]["current"]

        current_temp = str(int(data["feels_like"] - 273.15))

        size = d.textsize(current_temp, f)

        d.text(
            (
                self._matrix.dimensions[0] - size[0] - x_offset - radius - 1,
                y_offset
            ),
            current_temp,
            font=f,
            fill=color
        )

        d.rectangle(
            [
                self._matrix.dimensions[0] - radius - x_offset - 1,
                y_offset - 1,
                self._matrix.dimensions[0] - x_offset - 1,
                y_offset + radius - 1
            ],
            fill=color
        )

        icon = self.get_icon(data["weather"][0]["icon"], 10)

        self._temperature_image.paste(
            icon, 
            (
                self._matrix.dimensions[0] - size[0] - x_offset - icon.width - radius - 2, 
                y_offset - 4
            )
        )
        
    def draw_forecast(self):
        font_path = os.path.join(FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(self._temperature_image)
        
        data = weather_data[self._location]["daily"]

        x_offset = 1
        y_offset = 10

        neutral_color = (170, 170, 170)

        hot_color = "red"
        warm_color = "orange"
        cold_color = "lightblue"
        freezing_color = "blue"

        hot = 17
        freezing = -17

        block_width = 9
        icon_size= 4

        x = x_offset

        for i, forecast in enumerate(data):
            
            day = datetime.fromtimestamp(forecast["dt"]).strftime("%A")[0]
            day_size = d.textsize(day, f)

            day_x = x + (block_width // 2) - (day_size[0] // 2)
            day_y = y_offset

            d.text(
                (
                    day_x,
                    day_y
                ),
                day,
                font=f,
                fill=neutral_color
            )

            min_temp_int = int(forecast["temp"]["min"] - 273.15)
            max_temp_int = int(forecast["temp"]["max"] - 273.15)

            min_color = neutral_color
            if min_temp_int > 0:
                if min_temp_int >= hot:
                    min_color = hot_color
                else:
                    min_color = warm_color
            elif min_temp_int < 0:
                if min_temp_int <= freezing:
                    min_color = freezing_color
                else:
                    min_color = cold_color
                min_temp_int = abs(min_temp_int)

            max_color = neutral_color
            if max_temp_int > 0:
                if max_temp_int >= hot:
                    max_color = hot_color
                else:
                    max_color = warm_color
            elif max_temp_int < 0:
                if max_temp_int <= freezing:
                    max_color = freezing_color
                else:
                    max_color = cold_color
                max_temp_int = abs(max_temp_int)

            min_temp = str(min_temp_int)
            max_temp = str(max_temp_int)

            min_temp_size = d.textsize(min_temp, f)
            max_temp_size = d.textsize(max_temp, f)

            max_x = x + (block_width // 2) - (max_temp_size[0] // 2)
            max_y = y_offset + day_size[1]

            d.text(
                (
                    max_x,
                    max_y
                ),
                max_temp,
                font=f,
                fill=max_color
            )

            min_x = x + (block_width // 2) - (min_temp_size[0] // 2)
            min_y = y_offset + day_size[1] + max_temp_size[1]

            d.text(
                (
                    min_x,
                    min_y
                ),
                min_temp,
                font=f,
                fill=min_color
            )

            icon_x = x + (block_width // 2) - (icon_size // 2)
            icon_y = y_offset + day_size[1] + max_temp_size[1] + min_temp_size[1] + 2

            icon = self.get_icon(forecast["weather"][0]["icon"], icon_size)
            self._temperature_image.paste(
                icon, 
                (
                    icon_x, 
                    icon_y
                )
            )

            x += block_width

    def get_icon(self, code, size):
        path = os.path.join(SRC_BASE, "assets", "weatherview", "icons", f"{code}.png")
        image = Image.open(path)

        resized = image.resize((size, size), Image.BOX)

        return resized

def request_thread():
    global frames

    weather_data = WeatherData()
    radar_data = RadarData()

    while True:
        request_e.wait()
        radar_data.update()
        weather_data.update()
        request_e.clear()

class WeatherData():
    EXCLUDE = "minutely,hourly"

    def update(self):
        global weather_data

        for location in LOCATIONS:
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={location['lat']}&lon={location['lon']}&exclude={self.EXCLUDE}&appid={ENV_VALUES['OPENWEATHER_API_KEY']}"
            data = requests.get(url).json()

            weather_data[location["name"]] = data

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
        global radar_api_updated

        self.get_api_file()

        # Check if the API data changed.
        if self._api_file["generated"] == self._last_updated:
            return

        self._last_updated = self._api_file["generated"]

        new_frames.clear()

        self.get_past_radar()
        self.get_nowcast_radar()

        radar_api_updated = True

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