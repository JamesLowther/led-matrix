from PIL import Image, ImageDraw, ImageFont
import time
import numpy as np
from math import pi, sin, cos

class TestView:
    def __init__(self, matrix, press_event):
        self.matrix = matrix
        self._press_event = press_event

    def run(self):
        base = time.time()

        a = 6
        b = 23

        xyz = []
        R = 15
        MAP_WIDTH = 10
        MAP_HEIGHT = 49

        for i in range(MAP_HEIGHT + 1):
            lat = (pi / MAP_HEIGHT) * i
            for j in range(MAP_WIDTH + 1):
                lon = (2 * pi / MAP_WIDTH) * j
                x = round(R * sin(lat) * cos(lon), 2)
                y = round(R * sin(lat) * sin(lon), 2)
                z = round(R * cos(lat), 2)
                xyz.append((x, y, z))

        sphere = Object()
        sphere_nodes = [i for i in xyz]
        sphere.add_nodes(np.array(sphere_nodes))

        c = cos(1.5708)
        s = sin(1.5708)

        matrix_fix = np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]
        ])

        sphere.rotate(sphere.find_center(), matrix_fix)

        theta = 0.03
        bgcolor = "black"
        while not self._press_event.is_set():
            image = Image.new("RGB", self.matrix.dimensions, color=bgcolor)

            for node in sphere.nodes:
                # print(f"x:{node[0]} y:{node[1]}")
                if node[2] > 1:
                    image.putpixel((32 + int(node[0]), 16 + int(node[1])), (255, 255, 255, 255))

            # Update the rotation angle
            self.rotate_object(sphere, theta)

            # bgcolor = "black" if bgcolor == "gray" else "gray"

            self.matrix.set_image(image)

            time.sleep(0.03)

    def rotate_object(self, obj, theta):
        center = obj.find_center()

        c = np.cos(theta)
        s = np.sin(theta)

        matrix1 = np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ])

        matrix2 = np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]
        ])

        obj.rotate(center, matrix1)
        obj.rotate(center, matrix2)

class Object:
    def __init__(self):
        self.nodes = np.zeros((0, 4))

    def add_nodes(self, node_array):
        ones_column = np.ones((len(node_array), 1))
        ones_added = np.hstack((node_array, ones_column))
        self.nodes = np.vstack((self.nodes, ones_added))

    def find_center(self):
        mean = self.nodes.mean(axis=0)
        return mean

    def rotate(self, center, matrix):
        for i, node in enumerate(self.nodes):
            # print(f"before:{self.nodes[i]}")
            self.nodes[i] = center + np.matmul(matrix, node - center)
            # print(f"after:{self.nodes[i]}")
