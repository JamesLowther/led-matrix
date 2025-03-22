from PIL import Image, ImageChops, ImageOps, ImageFont, ImageDraw
import time
import numpy as np
from math import pi, sin, cos, radians
import json

from config import Config
from common import msleep
import os
import requests
import threading

request_e = threading.Event()
iss_coords = (0, 0)
number_ast = 0
api_error = False

class ISSView:
    REFRESH_INTERVAL = 150 # ms.
    API_INTERVAL= 5 # s.
    BG_COLOUR = "black"

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

        # Start the request thread.
        self._request_t = threading.Thread(name="requests", target=request_thread)
        self._request_t.daemon = True
        self._request_t.start()

        request_e.set()

        self._earth = Earth()
        self._earth.update_iss()

    def run(self):
        """
        Starts the ISSView.
        """
        start_time = time.time()

        while not self._press_event.is_set():
            current_time = time.time()
            if current_time - start_time >= self.API_INTERVAL:
                start_time = current_time
                request_e.set()

            image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOUR)

            self.draw_time(image)
            self.draw_coords(image)
            self.draw_ast(image)

            if api_error:
                self.draw_error(image)

            self._earth.draw(image)
            self._earth.update_spin()

            self._matrix.set_image(image)

            msleep(self.REFRESH_INTERVAL)

    def draw_time(self, image):
        """
        Draws the current time.
        """

        x_offset = 2
        y_offset = 1

        color = (170, 170, 170)

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


    def draw_coords(self, image):
        """
        Draws the latitude and longitude on the the screen.
        """
        font_path = os.path.join(Config.FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(image)

        color = (170, 170, 170)

        x_offset = 2
        y_offset = 11

        spacing = 7

        truncate_len = 6

        # Draw latitude.
        lat = str(round(iss_coords[0], 3))
        if len(lat) > truncate_len:
            lat = lat[:truncate_len]

        d.text(
            (x_offset, y_offset),
            lat,
            font=f,
            fill=color
        )

        # Draw longitude.
        lon = str(round(iss_coords[1], 3))
        if len(lon) > truncate_len:
            lon = lon[:truncate_len]

        d.text(
            (x_offset, y_offset + spacing),
            lon,
            font=f,
            fill=color
        )

    def draw_ast(self, image):
        """
        Draw icons for each astronaut on the ISS.
        """
        x_offset = 2
        y_offset = 28

        size = 2
        x_spacing = 2
        y_spacing = 1

        line_length = 7

        colors = [
            "darkred",
            "green",
            "purple",
            "darkgoldenrod",
            "teal",
            "indigo",
            "darkslategrey",
            "olivedrab",
            "sienna",
            "mediumorchid"
        ]

        if number_ast > line_length:
            y_offset -= 2

        d = ImageDraw.Draw(image)

        for i in range(min(line_length, number_ast)):
            d.rectangle(
                [
                    x_offset + ((size + x_spacing) * i),
                    y_offset,
                    x_offset + ((size + x_spacing) * i) + size - 1,
                    y_offset + size - 1
                ],
                fill=colors[i % len(colors)]
            )

        if number_ast > line_length:
            for i in range(number_ast - line_length):
                d.rectangle(
                    [
                        x_offset + ((size + x_spacing) * i),
                        y_offset + (size + y_spacing),
                        x_offset + ((size + x_spacing) * i) + size - 1,
                        y_offset + size - 1 + (size + y_spacing)
                    ],
                    fill=colors[(line_length + i) % len(colors)]
                )

    def draw_error(self, image):
        """
        Draws the error indicator if there are connection problems with the API.
        """

        x_offset = 59
        y_offset = 27

        circle_d = 3

        color = "darkred"

        d = ImageDraw.Draw(image)

        d.ellipse(
            [
                x_offset,
                y_offset,
                x_offset + circle_d,
                y_offset + circle_d
            ],
            outline=color
        )

        d.line(
            [
                x_offset + 1,
                y_offset + 1,
                x_offset + circle_d - 1,
                y_offset + circle_d - 1
            ],
            fill=color
        )

class Earth:
    HOME_COORDS = (51.030436, -114.065720)

    EARTH_COLOR = (255, 171, 145, 255)
    ISS_COLOR = (255, 0, 0, 255)
    HOME_COLOR = (0, 255, 0, 255)

    MAP_CALIBRATION = 1

    RADIUS = 13
    MAP_WIDTH = 80
    MAP_HEIGHT = 40

    X = 46
    Y = 15

    SPIN_THETA = 0.05

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
        """
        Converts latitude and longitude to Cartesian coordinates.
        In this case the y coordinate is on the vertical plane
        and x and z are on the horizontal plane.
        """
        x = round(self.RADIUS * sin(lat) * cos(lon), 2)
        y = round(self.RADIUS * cos(lat), 2)
        z = round(self.RADIUS * sin(lat) * sin(lon), 2)

        return (x, y, z)

    def add_nodes(self):
        """
        Generates the nodes used to display the Earth and stores them in an array.
        Backups of the arrays are saved so they can be restored on each rotation.
        """
        xyz = []

        # Map to Cartesian plane.
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
        """
        Returns the center coordinates of the Earth.
        """
        return self._earth_nodes.mean(axis=0)

    def update_iss(self):
        """
        Generates a new array of nodes to store the location of the ISS.
        """
        self.update_coords()

        ones_column = np.ones((1, 1))
        ones_added = np.hstack(([self._iss_coords], ones_column))
        self._iss_nodes = np.vstack((np.zeros((0, 4)), ones_added))

    def update_spin(self):
        """
        Handles the logic to control the Earth rotation.
        Resets the nodes to the backed-up version after every full rotation.
        """
        self._current_spin += self.SPIN_THETA

        # Earth has done a full rotation. Reset the nodes for alignment.
        if self._current_spin >= 2 * pi:
            self._current_spin = 0
            self._earth_nodes = np.copy(self._earth_nodes_backup)
            self._home_nodes = np.copy(self._home_nodes_backup)
            self.update_iss()

        # Rotate counter-clockwise as normal.
        else:
            c = np.cos(self.SPIN_THETA)
            s = np.sin(self.SPIN_THETA)

            matrix_y = np.array([
                [c, 0, s, 0],
                [0, 1, 0, 0],
                [-s, 0, c, 0],
                [0, 0, 0, 1]
            ])

            self.rotate(matrix_y)

    def rotate(self, matrix):
        """
        Applies the rotation matrix to the Earth array, ISS array, and home array.
        """
        center = self.find_center()

        for i, node in enumerate(self._earth_nodes):
            self._earth_nodes[i] = center + np.matmul(matrix, node - center)

        self._iss_nodes[0] = center + np.matmul(matrix, self._iss_nodes[0] - center)
        self._home_nodes[0] = center + np.matmul(matrix, self._home_nodes[0] - center)

    def draw(self, image):
        """
        Draws the Earth, ISS, and home node arrays to the display.
        """
        # Draw the Earth.
        for i, node in enumerate(self._earth_nodes):
            if (i > self.MAP_WIDTH - 1 and
                i < (self.MAP_WIDTH * self.MAP_HEIGHT - self.MAP_WIDTH) and
                node[2] > 1 and self._map[i][0]):
                image.putpixel(
                    (self.X + int(node[0]),
                    self.Y + int(node[1]) * -1),
                    self._map[i][1]
                )

        # Draw the ISS.
        iss_x = int(self._iss_nodes[0][0])
        iss_y = int(self._iss_nodes[0][1])
        iss_z = self._iss_nodes[0][2]

        if iss_z > 1:
            image.putpixel((self.X + iss_x, self.Y + iss_y * -1), self.ISS_COLOR)

        # Draw home.
        home_x = int(self._home_nodes[0][0])
        home_y = int(self._home_nodes[0][1])
        home_z = self._home_nodes[0][2]

        if home_z > 1:
            image.putpixel((self.X + home_x, self.Y + home_y * -1), self.HOME_COLOR)

    def add_tilt(self):
        """
        Adds tilt to the nodes to the Earth and returns the new array.
        Not currently used.
        """
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
        """
        Converts the PNG image of the world map to one that can be projected onto the sphere.
        Turns the pixels in an array of bits.
        """
        # Open the map image.
        path = os.path.join(Config.SRC_BASE, "assets", "iss_view", "world-map.png")
        img = Image.open(path).convert("RGB")

        # Transform the image to fit sphere dimensions.
        resized = img.resize((self.MAP_WIDTH + 1, self.MAP_HEIGHT + 1), Image.BOX)
        flipped = ImageOps.mirror(resized)
        shifted = ImageChops.offset(flipped, self.MAP_CALIBRATION, 0)

        # Convert to bit array.
        for y in range(shifted.height):
            for x in range(shifted.width):
                pixel = shifted.getpixel((x, y))
                self._map.append((int(pixel != (0, 0, 0)), self.EARTH_COLOR))

    def update_coords(self):
        """
        Updates the coordinates for the ISS.
        """
        global iss_coords
        self._iss_coords = self.convert_coords(radians(90 - iss_coords[0]), radians(180 - iss_coords[1]))

def request_thread():
    global iss_coords
    global number_ast
    global api_error
    api_connection = APIConnection()

    while True:
        request_e.wait()
        iss_return = api_connection.get_iss_coords()
        ast_return = api_connection.get_ast_number()

        api_error = iss_return == None or ast_return == None

        if iss_return != None:
            iss_coords = iss_return

        if ast_return != None:
            number_ast = ast_return

        request_e.clear()

class APIConnection:
    ISS_ENDPOINT = "http://api.open-notify.org/iss-now.json"
    AST_ENDPOINT = "http://api.open-notify.org/astros.json"

    def get_iss_coords(self):
        """
        Sends a request to the ISS API to get its location.
        """
        try:
            loc = requests.get(self.ISS_ENDPOINT).json()
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError):
            return None

        return (float(loc["iss_position"]["latitude"]), float(loc["iss_position"]["longitude"]))

    def get_ast_number(self):
        """
        Sends a request to get the number of astronauts on the ISS.
        """
        try:
            results = requests.get(self.AST_ENDPOINT).json()
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError):
            return None

        count = 0
        for person in results["people"]:
            if person["craft"] == "ISS":
                count += 1

        return count
