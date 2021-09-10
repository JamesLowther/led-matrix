from PIL import Image
import time
import numpy as np
from math import pi, sin, cos, radians
from cfg import SRC_BASE
import os
import requests

class ISSView():
    REFRESH_INTERVAL = 50 # ms.
    API_INTERVAL= 30 # s.
    BG_COLOUR = "black"

    def __init__(self, matrix):
        self._matrix = matrix
        self._earth = Earth()
        self._api = APIConnection()
        self._coords = self.update_iss_coords()

    def run(self):
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time >= self.API_INTERVAL:
                start_time = current_time
                self.update_iss_coords()

            image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOUR)

            self._earth.draw(image)
            self._earth.update_spin(0.05)
            self._matrix.set_image(image)

            self.msleep(self.REFRESH_INTERVAL)

    def update_iss_coords(self):
        self._coords = self._api.get_coords()
        self._earth.update_coords(self._coords)

    def msleep(self, ms):
        time.sleep(ms / 1000)

class Earth():
    RADIUS = 13
    MAP_WIDTH = 80
    MAP_HEIGHT = 40
    # MAP_WIDTH = 25
    # MAP_HEIGHT = 25
    X = 46
    Y = 15

    def __init__(self):
        self._nodes = np.zeros((0, 4))
        self._map = []
        self._coords = None
        self._coord_index = 2000
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

        node_array = np.array(xyz)

        ones_column = np.ones((len(node_array), 1))
        ones_added = np.hstack((node_array, ones_column))
        self._nodes = np.vstack((self._nodes, ones_added))

        # Terrible orientation fix.
        c = cos(1.5708)
        s = sin(1.5708)
        matrix_fix = np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]
        ])

        # self.rotate(matrix_fix)    
        self._nodes_backup = np.copy(self._nodes)

    def find_center(self):
        return self._nodes.mean(axis=0)

    def update_spin(self, theta):
        c = np.cos(theta)
        s = np.sin(theta)

        matrix_y = np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ])    

        # matrix_z = np.array([
        #     [1, 0, 0, 0],
        #     [0, c, -s, 0],
        #     [0, s, c, 0],
        #     [0, 0, 0, 1]
        # ])

        self.rotate(matrix_y)
        # self.rotate(matrix_z)

    def rotate(self, matrix):
        center = self.find_center()

        for i, node in enumerate(self._nodes):
            self._nodes[i] = center + np.matmul(matrix, node - center)

        self._coords[0] = center + np.matmul(matrix, self._coords[0] - center)

    def draw(self, image):
        for i, node in enumerate(self._nodes):
            if i > self.MAP_WIDTH - 1 and i < (self.MAP_WIDTH * self.MAP_HEIGHT - self.MAP_WIDTH) and node[2] > 1 and self._map[i]:
                image.putpixel((self.X + int(node[0]), self.Y + int(node[1]) * -1), (255, 255, 255, 255))

        iss_x = int(self._coords[0][0])
        iss_y = int(self._coords[0][1])
        iss_z = self._coords[0][2]

        if iss_z > 1:
            image.putpixel((self.X + iss_x, self.Y + iss_y), (255, 0, 0, 255))

    def add_tilt(self):
        # angle = 0.4101524
        angle = 0

        c = np.cos(angle)
        s = np.sin(angle)
        
        matrix_x = np.array([
            [c, -s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        temp_nodes = np.copy(self._nodes)

        center = self.find_center()

        for i, node in enumerate(temp_nodes):
            temp_nodes[i] = center + np.matmul(matrix_x, node - center)

        return temp_nodes

    def convert_map(self):
        path = os.path.join(SRC_BASE, "assets", "issview", "world-map.png")
        img = Image.open(path).convert("1")
        img.save("output.png", "PNG")

        resized = img.resize((self.MAP_WIDTH + 1, self.MAP_HEIGHT + 1), Image.BOX)

        for y in range(resized.height):
            for x in range(resized.width):
                pixel = resized.getpixel((x, y))
                if pixel == 255:
                    self._map.append(1)
                else:
                    self._map.append(0)

    def update_coords(self, coords):
        coords = [self.convert_coords(radians(coords[0]), radians(coords[1]))]

        ones_column = np.ones((len(coords), 1))
        ones_added = np.hstack((coords, ones_column))
        self._coords = np.vstack((np.zeros((0, 4)), ones_added))

        print(self._coords)

class APIConnection():
    def __init__(self):
        pass

    def get_coords(self):
        loc = requests.get("http://api.open-notify.org/iss-now.json").json()

        return (float(loc["iss_position"]["latitude"]), float(loc["iss_position"]["longitude"]))