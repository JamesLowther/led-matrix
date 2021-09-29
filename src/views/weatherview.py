from PIL import Image, ImageDraw
from io import BytesIO

import time
import requests
import threading

request_e = threading.Event()

new_frames = []
api_updated = False

api_error = False

class WeatherView():
    FRAME_INTERVAL = 1100 #  ms.
    API_INTERVAL = 5 # s.

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

        self._frames = []

        self._request_t = threading.Thread(name="requests", target=request_thread)
        self._request_t.daemon = True
        self._request_t.start()

        request_e.set()

    def run(self):
        # Wait for initial frame data to be generated.
        while(not api_updated):
            time.sleep(0.1)

        self.update_frames()

        start_time = time.time()

        i = 0
        while not self._press_event.is_set():
            current_time = time.time()
            if current_time - start_time >= self.API_INTERVAL:
                start_time = current_time
                request_e.set()

            if i == 0 and api_updated:
                self.update_frames()

            current_image = self._frames[i]
            self.draw_location(current_image)
            self._matrix.set_image(self._frames[i])

            i = (i + 1) % len(self._frames)

            self.msleep(self.FRAME_INTERVAL)

    def update_frames(self):
        global api_updated
        self._frames = new_frames.copy()
        api_updated = False

    def draw_location(self, image):

        x_offset = 31 
        y_offset = 15

        w = 2
        h = 2

        color = "lightblue"

        d = ImageDraw.Draw(image)

        d.rectangle(
            [
                x_offset,
                y_offset,
                x_offset + w - 1,
                y_offset + h - 1
            ],
            fill=color
        )

    def msleep(self, ms):
        """
        Sleep in milliseconds.
        """
        time.sleep(ms / 1000)

def request_thread():
    global frames

    radar_data = RadarData()

    while True:
        request_e.wait()
        
        radar_data.update()

        request_e.clear()


class RadarData():
    API_FILE_URL = "https://api.rainviewer.com/public/weather-maps.json"
    
    NUMBER_PAST = 4
    NUMBER_NOWCAST = 3

    LATITUDE = 51.030436
    LONGITUDE = -114.065720

    ZOOM = 5
    COLOR = 1
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

        past_api_data = self._api_file["radar"]["past"][number_data - self.NUMBER_PAST - 1:]
        
        for data in past_api_data:
            url = f"{self._api_file['host']}{data['path']}/{size}/{self.ZOOM}/{self.LATITUDE}/{self.LONGITUDE}/{self.COLOR}/{self.SMOOTH}_{self.SNOW}.png"
            radar_image = requests.get(url)

            img = Image.open(BytesIO(radar_image.content))
            converted_image = self.convert_image(img)

            new_frames.append(converted_image)

    def get_nowcast_radar(self):
        size = 512

        number_data = len(self._api_file["radar"]["nowcast"])

        nowcast_api_data = self._api_file["radar"]["nowcast"][number_data - self.NUMBER_NOWCAST - 1:]
        
        for data in nowcast_api_data:
            url = f"{self._api_file['host']}{data['path']}/{size}/{self.ZOOM}/{self.LATITUDE}/{self.LONGITUDE}/{self.COLOR}/{self.SMOOTH}_{self.SNOW}.png"
            radar_image = requests.get(url)

            img = Image.open(BytesIO(radar_image.content))
            converted_image = self.convert_image(img)

            new_frames.append(converted_image)

    def convert_image(self, image):
        resized = image.resize((64, 64), Image.BOX)
        cropped = resized.crop((0, 15, 64, 47))
        return cropped

