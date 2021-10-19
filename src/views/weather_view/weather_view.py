from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from config import Config

from common import msleep
from transitions import Transitions
from views.weather_view.radar_view import RadarView
from views.weather_view.temperature_view import TemperatureView
from views.weather_view.wind_view import WindView

import time
import requests
import threading

request_e = threading.Event()

new_frames = []
last_updated = 0
radar_api_updated = False

weather_data = {}
weather_api_updated = False

radar_api_error = False
weather_api_error = False

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
    },
    {
        "name": "Berlin",
        "lat": 52.5200,
        "lon": 13.4050
    },
    {
        "name": "London",
        "lat": 51.5074,
        "lon": -0.1278
    }
]

WIND_LOCATION = "Calgary"

class WeatherView():
    FRAME_INTERVAL = 1300 # ms.
    HOLD_TIME = 2600 # ms.
    
    FORECAST_INTERVAL = 16000 # ms.

    WIND_INTERVAL = 30000 # ms.

    RADAR_LOOPS = 5

    API_INTERVAL = 300 # s.

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

        self._start_time = time.time()

        self._frames = []

        self._request_t = threading.Thread(name="requests", target=request_thread)
        self._request_t.daemon = True
        self._request_t.start()

        self._radar_view = RadarView(self._matrix)

        self._location_temperature_views = []
        for location in LOCATIONS:
            self._location_temperature_views.append(
                TemperatureView(self._matrix, location["name"])
            )

        self._wind_view = WindView(self._matrix)

    def run(self):
        global last_updated
        global radar_api_updated
        global radar_api_error
        global weather_api_error

        last_updated = 0
        request_e.set()

        radar_api_error = True

        # Wait for initial frame data to be generated.
        while(not radar_api_updated and not radar_api_error and len(self._frames) == 0):
            msleep(200)

        self.check_update()

        prev_image = None
        while not self._press_event.is_set():

            self.check_update()
            if not radar_api_error:
                prev_image = self.start_radar_loop(prev_image)
                if prev_image == -1:
                    return

            # Ensure that weather api data gets set.
            while len(weather_data) != len(LOCATIONS) and not weather_api_error:
                msleep(200)

            if not weather_api_error:
                self.check_update()
                prev_image = self.start_temperature_loop(prev_image)
                if prev_image == -1:
                    return
                
                self.check_update()
                prev_image = self.start_wind_loop(prev_image)
                if prev_image == -1:
                    return
            
    def start_radar_loop(self, prev_image):
        current_image = None
        for _ in range(self.RADAR_LOOPS):
            for radar_i in range(len(self._frames)):
                current_image = self._frames[radar_i]["frame"]
                current_time = self._frames[radar_i]["time"]

                self._radar_view.generate_radar_image(current_image, current_time)

                if prev_image == None:
                    self._matrix.set_image(current_image, unsafe=False)
                    msleep(self.FRAME_INTERVAL)

                else:
                    Transitions.vertical_transition(self._matrix, prev_image, current_image)
                    prev_image = None
                    msleep(self.HOLD_TIME)

                if self._press_event.is_set():
                    return -1

            msleep(self.HOLD_TIME - self.FRAME_INTERVAL)

        return current_image

    def start_temperature_loop(self, prev_image):
        for i, location in enumerate(self._location_temperature_views):
            next_image = location.generate_temperature_image(weather_data)
            self.check_api_interval()
            if prev_image != None:
                if i == 0:
                    Transitions.vertical_transition(self._matrix, prev_image, next_image)

                else:
                    Transitions.horizontal_transition(self._matrix, prev_image, next_image)
            else:
                self._matrix.set_image(next_image, unsafe=False)

            start_time = time.time()

            while time.time() - start_time <= (self.FORECAST_INTERVAL / 1000):
                msleep(500)

                if self._press_event.is_set():
                    return -1

            prev_image = next_image

        return prev_image

    def start_wind_loop(self, prev_image):
        sleep = 50

        self.check_api_interval()

        self._wind_view.initialize_particles(weather_data[WIND_LOCATION]["current"]["wind_speed"])

        next_image = self._wind_view.generate_wind_image()

        Transitions.horizontal_transition(self._matrix, prev_image, next_image)

        start_time = time.time()
        while time.time() - start_time <= (self.WIND_INTERVAL / 1000):
            next_image = self._wind_view.generate_wind_image()
            self._matrix.set_image(next_image)
            msleep(sleep)

            if self._press_event.is_set():
                    return -1

        return next_image

    def check_api_interval(self):
        current_time = time.time()
        if current_time - self._start_time >= self.API_INTERVAL:
            self._start_time = current_time
            request_e.set()

    def check_update(self):
        global radar_api_updated
        if radar_api_updated:
            self.update_frames()

    def update_frames(self):
        global radar_api_updated
        global new_frames

        self._frames = new_frames.copy()
        radar_api_updated = False

def request_thread():
    global frames
    global radar_api_error
    global weather_api_error

    weather_data = WeatherData()
    radar_data = RadarData()

    while True:
        request_e.wait()
        radar_data_result = radar_data.update()
        weather_data_result = weather_data.update()

        if radar_data_result == False:
            radar_api_error = True
        else:
            radar_api_error = False

        if weather_data_result == False:
            weather_api_error = True
        else:
            weather_api_error = False

        request_e.clear()

class WeatherData():
    EXCLUDE = "minutely,hourly"

    RETRY_TIME = 2000

    def update(self, retry_attempts=3):
        global weather_data

        for location in LOCATIONS:
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={location['lat']}&lon={location['lon']}&exclude={self.EXCLUDE}&appid={Config.ENV_VALUES['OPENWEATHER_API_KEY']}"
            
            for i in range(retry_attempts):
                try:
                    data = requests.get(url).json()
                    break
                except requests.exceptions.RequestException:
                    if i + 1 == retry_attempts:
                        return False

                    msleep(self.RETRY_TIME)

            weather_data[location["name"]] = data

        weather_api_updated = True

class RadarData():
    API_FILE_URL = "https://api.rainviewer.com/public/weather-maps.json"
    
    RETRY_TIME = 2000

    NUMBER_PAST = 5     # Max 12.
    NUMBER_NOWCAST = 3  # Max 3.

    LATITUDE = 51.030436
    LONGITUDE = -114.065720

    ZOOM = 5
    COLOR = 2
    SMOOTH = 0
    SNOW = 1

    def __init__(self):
        self._api_file = None
    
    def update(self):
        global radar_api_updated
        global last_updated
        global new_frames

        if self.get_api_file() == False:
            return False

        # Check if the API data changed.
        if self._api_file["generated"] == last_updated:
            return

        last_updated = self._api_file["generated"]

        new_frames.clear()
        if self.get_past_radar() == False:
            return False
        
        if self.get_nowcast_radar() == False:
            return False

        radar_api_updated = True

    def get_api_file(self, retry_attempts=3):
        for i in range(retry_attempts):
            try:
                self._api_file = requests.get(self.API_FILE_URL).json()
                break
            except requests.exceptions.RequestException:
                if i + 1 == retry_attempts:
                    return False
                msleep(self.RETRY_TIME)

    def get_past_radar(self, retry_attempts=3):
        global new_frames

        size = 512

        number_data = len(self._api_file["radar"]["past"])

        past_api_data = self._api_file["radar"]["past"][number_data - self.NUMBER_PAST:]
        
        for data in past_api_data:
            url = f"{self._api_file['host']}{data['path']}/{size}/{self.ZOOM}/{self.LATITUDE}/{self.LONGITUDE}/{self.COLOR}/{self.SMOOTH}_{self.SNOW}.png"
            
            radar_image = None
            for i in range(retry_attempts):
                try:
                    radar_image = requests.get(url)
                    break
                except requests.exceptions.RequestException:
                    if i + 1 == retry_attempts:
                        return False
                    msleep(self.RETRY_TIME)

            img = Image.open(BytesIO(radar_image.content))
            converted_image = self.convert_image(img)

            new_frames.append(
                {
                    "time": data["time"],
                    "frame": converted_image
                }
            )

    def get_nowcast_radar(self, retry_attempts=3):
        global new_frames

        size = 512

        number_data = len(self._api_file["radar"]["nowcast"])

        nowcast_api_data = self._api_file["radar"]["nowcast"][number_data - self.NUMBER_NOWCAST:]
        
        for data in nowcast_api_data:
            url = f"{self._api_file['host']}{data['path']}/{size}/{self.ZOOM}/{self.LATITUDE}/{self.LONGITUDE}/{self.COLOR}/{self.SMOOTH}_{self.SNOW}.png"
            
            radar_image = None
            for i in range(retry_attempts):
                try:
                    radar_image = requests.get(url)
                    break
                except requests.exceptions.RequestException:
                    if i == retry_attempts:
                        return False
                    msleep(self.RETRY_TIME)

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
