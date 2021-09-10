from PIL import Image, ImageChops, ImageOps, ImageFont, ImageDraw
import time
import numpy as np
from math import pi, sin, cos, radians
from cfg import SRC_BASE
import os
import requests
import threading

e = threading.Event()
iss_coords = (0, 0)

class ISSView():
    REFRESH_INTERVAL = 50 # ms.
    API_INTERVAL= 2 # s.
    BG_COLOUR = "black"

    def __init__(self, matrix):
        self._matrix = matrix

        self._request_t = threading.Thread(name="requests", target=request_thread, args=(e,))
        self._request_t.start()

        e.set()

        self._earth = Earth()
        self._iss_nodes = self.update_iss_coords()
        self._earth.update_iss()

    def run(self):
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time >= self.API_INTERVAL:
                start_time = current_time
                self.update_iss_coords()

            image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOUR)

            self.draw_coords(image)

            self._earth.draw(image)
            self._earth.update_spin(0.05)
            
            self._matrix.set_image(image)

            self.msleep(self.REFRESH_INTERVAL)

    def draw_coords(self, image):
        font_path = os.path.join(SRC_BASE, "assets", "fonts", "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(image)

        color = (184, 184, 184)

        x_offset = 1
        y_offset = 8

        # Latitude.
        d.text(
            (x_offset, y_offset),
            str(round(iss_coords[0], 3)),
            font=f,
            fill=color
        )

        # Longitude.
        d.text(
            (x_offset, y_offset + 10),
            str(round(iss_coords[1], 3)),
            font=f,
            fill=color
        )

    def update_iss_coords(self):
        e.set()

    def msleep(self, ms):
        time.sleep(ms / 1000)

class Earth():
    HOME_COORDS = (51.030436, -114.065720)

    MAP_CALIBRATION = 1
    RADIUS = 13
    MAP_WIDTH = 80
    MAP_HEIGHT = 40
    # MAP_WIDTH = 25
    # MAP_HEIGHT = 25
    X = 49
    Y = 15

    def __init__(self):
        # Used for drawing the Earth.
        self._earth_nodes = np.zeros((0, 4))
        self._earth_nodes_backup = None
        self._map = []

        # Used for drawing the ISS.
        self._iss_coords = None
        self._iss_nodes = None

        # Used for drawing my coords.
        self._home_nodes = None
        self._home_nodes_backup = None

        self._current_spin = 0
        
        self.add_nodes()
        self.convert_map()
    
    def convert_coords(self, lat, lon):
        x = round(self.RADIUS * sin(lat) * cos(lon), 2)
        y = round(self.RADIUS * cos(lat), 2)
        z = round(self.RADIUS * sin(lat) * sin(lon), 2)
        
        return (x, y, z)

    def add_nodes(self):
        xyz = []

        # Map to Cartesian plane
        for i in range(self.MAP_HEIGHT + 1):
            lat = (pi / self.MAP_HEIGHT) * i
            for j in range(self.MAP_WIDTH + 1):
                lon = (2 * pi / self.MAP_WIDTH) * j
                xyz.append(self.convert_coords(lat, lon))

        # Build the array of nodes.
        node_array = np.array(xyz)
        ones_column = np.ones((len(node_array), 1))
        ones_added = np.hstack((node_array, ones_column))
        self._earth_nodes = np.vstack((self._earth_nodes, ones_added))

        # Build home array of nodes.
        home_coords = self.convert_coords(radians(90 - self.HOME_COORDS[0]), radians(180 - self.HOME_COORDS[1]))
        ones_column = np.ones((1, 1))
        ones_added = np.hstack(([home_coords], ones_column))
        self._home_nodes = np.vstack((np.zeros((0, 4)), ones_added))

        # Backup the nodes to allow them to be restored after full rotation.
        self._earth_nodes_backup = np.copy(self._earth_nodes)
        self._home_nodes_backup = np.copy(self._home_nodes)

    def find_center(self):
        return self._earth_nodes.mean(axis=0)

    def update_iss(self):
        self.update_coords()

        ones_column = np.ones((1, 1))
        ones_added = np.hstack(([self._iss_coords], ones_column))
        self._iss_nodes = np.vstack((np.zeros((0, 4)), ones_added))

    def update_spin(self, theta):
        self._current_spin += theta

        # Earth has done a full rotation. Reset the nodes for alignment.
        if self._current_spin >= 2 * pi:
            self._current_spin = 0
            self._earth_nodes = np.copy(self._earth_nodes_backup)
            self._home_nodes = np.copy(self._home_nodes_backup)
            self.update_iss()

        # Rotate counter-clockwise as normal.
        else:
            c = np.cos(theta)
            s = np.sin(theta)

            matrix_y = np.array([
                [c, 0, s, 0],
                [0, 1, 0, 0],
                [-s, 0, c, 0],
                [0, 0, 0, 1]
            ])    

            self.rotate(matrix_y)

    def rotate(self, matrix):
        center = self.find_center()

        for i, node in enumerate(self._earth_nodes):
            self._earth_nodes[i] = center + np.matmul(matrix, node - center)

        self._iss_nodes[0] = center + np.matmul(matrix, self._iss_nodes[0] - center)
        self._home_nodes[0] = center + np.matmul(matrix, self._home_nodes[0] - center)

    def draw(self, image):
        # Draw the Earth.
        for i, node in enumerate(self._earth_nodes):
            if i > self.MAP_WIDTH - 1 and i < (self.MAP_WIDTH * self.MAP_HEIGHT - self.MAP_WIDTH) and node[2] > 1 and self._map[i]:
                image.putpixel((self.X + int(node[0]), self.Y + int(node[1]) * -1), (255, 255, 255, 255))

        # Draw the ISS.
        iss_x = int(self._iss_nodes[0][0])
        iss_y = int(self._iss_nodes[0][1])
        iss_z = self._iss_nodes[0][2]

        if iss_z > 1:
            image.putpixel((self.X + iss_x, self.Y + iss_y * -1), (255, 0, 0, 255))

        # Draw home.
        home_x = int(self._home_nodes[0][0])
        home_y = int(self._home_nodes[0][1])
        home_z = self._home_nodes[0][2]

        if home_z > 1:
            image.putpixel((self.X + home_x, self.Y + home_y * -1), (0, 255, 0, 255))

    def add_tilt(self):
        angle = 0.4101524

        c = np.cos(angle)
        s = np.sin(angle)
        
        matrix_x = np.array([
            [c, -s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        tilted_nodes = np.copy(self._earth_nodes)

        center = self.find_center()

        for i, node in enumerate(tilted_nodes):
            tilted_nodes[i] = center + np.matmul(matrix_x, node - center)

        return tilted_nodes

    def convert_map(self):
        # Open the map image.
        path = os.path.join(SRC_BASE, "assets", "issview", "world-map.png")
        img = Image.open(path).convert("1")

        # Transform the image to fit sphere dimensions.
        resized = img.resize((self.MAP_WIDTH + 1, self.MAP_HEIGHT + 1), Image.BOX)
        flipped = ImageOps.mirror(resized)
        shifted = ImageChops.offset(flipped, self.MAP_CALIBRATION, 0)

        # Convert to bit array.
        for y in range(shifted.height):
            for x in range(shifted.width):
                pixel = shifted.getpixel((x, y))
                self._map.append(int(pixel == 255))
                    
    def update_coords(self):
        global iss_coords
        self._iss_coords = self.convert_coords(radians(90 - iss_coords[0]), radians(180 - iss_coords[1]))

def request_thread(e):
    global iss_coords
    api_connection = APIConnection()

    while True:
        e.wait()
        
        iss_coords = api_connection.get_coords()

        # Reset the event.
        e.clear()
        
class APIConnection():
    ENDPOINT = "http://api.open-notify.org/iss-now.json"

    def __init__(self):
        pass

    def get_coords(self):
        loc = requests.get(self.ENDPOINT).json()
        return (float(loc["iss_position"]["latitude"]), float(loc["iss_position"]["longitude"]))