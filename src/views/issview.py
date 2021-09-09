from PIL import Image
import time
import numpy as np
from math import pi, sin, cos

class ISSView():
    REFRESH_INTERVAL = 50
    BG_COLOUR = "#1c1c1c"

    def __init__(self, matrix):
        self._matrix = matrix
        self._earth = Earth()

    def run(self):
        while True:
            image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOUR)

            self._earth.draw(image)

            self._earth.update_spin(0.05)
            
            self._matrix.set_image(image)

            self.msleep(self.REFRESH_INTERVAL)

    def msleep(self, ms):
        time.sleep(ms / 1000)

class Earth():
    RADIUS = 14
    MAP_WIDTH = 25
    MAP_HEIGHT = 15
    X = 46
    Y = 15

    def __init__(self):
        self._nodes = np.zeros((0, 4))
        self.add_nodes()

    def add_nodes(self):
        xyz = []

        # Map to Cartesian plane
        for i in range(self.MAP_HEIGHT + 1):
            lat = (pi / self.MAP_HEIGHT) * i
            for j in range(self.MAP_WIDTH + 1):
                lon = (2 * pi / self.MAP_WIDTH) * j
                x = round(self.RADIUS * sin(lat) * cos(lon), 2)
                y = round(self.RADIUS * sin(lat) * sin(lon), 2)
                z = round(self.RADIUS * cos(lat), 2)
                xyz.append((x, y, z))

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

        self.rotate(matrix_fix)

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

    def rotate(self, matrix):
        center = self.find_center()

        for i, node in enumerate(self._nodes):
            self._nodes[i] = center + np.matmul(matrix, node - center)

    def draw(self, image):
        
        temp_nodes = self.add_tilt()

        for node in temp_nodes:
            if node[2] > 1:
                image.putpixel((self.X + int(node[0]), self.Y + int(node[1])), (255, 255, 255, 255))

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

        temp_nodes = np.copy(self._nodes)

        center = self.find_center()

        for i, node in enumerate(temp_nodes):
            temp_nodes[i] = center + np.matmul(matrix_x, node - center)

        return temp_nodes
