from PIL import Image, ImageDraw, ImageFont
import time
import os
from cfg import SRC_BASE
import numpy as np

class TestView():
    def __init__(self, matrix):
        self.matrix = matrix

    def run(self):
        base = time.time()

        a = 6
        b = 23

        cube = Object()
        cube_nodes = ([(x, y, z) for x in (a, b) for y in (a, b) for z in (a, b)])
        cube.add_nodes(np.array(cube_nodes))

        theta = 0.10
        bgcolor = "gray"
        while True:
            image = Image.new("RGB", self.matrix.dimensions, color=bgcolor)

            for node in cube.nodes:
                # print(f"x:{node[0]} y:{node[1]}")
                image.putpixel((int(node[0]), int(node[1])), (255, 255, 255, 255))

            # Update the rotation angle
            self.rotate_object(cube, theta)

            # bgcolor = "black" if bgcolor == "gray" else "gray"

            self.matrix.set_image(image)

            time.sleep(0.03)

    def rotate_object(self, obj, theta):
        center = obj.find_center()

        c = np.cos(theta)
        s = np.sin(theta)

        # matrix = np.array([
        #     [c, -s, 0, 0],
        #     [s, c, 0, 0],
        #     [0, 0, 1, 0],
        #     [0, 0, 0, 1]
        # ])   
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