from PIL import ImageDraw, ImageFont
from datetime import datetime
import os

from config import Config

class RadarView:
    LOCATION_COLOR = "lightsteelblue"

    def __init__(self, matrix):
        self._matrix = matrix

    def generate_radar_image(self, image, time):
        self.draw_location(image)
        self.draw_borders(image)
        self.draw_time(image, time)

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

    def draw_borders(self, image):
        d = ImageDraw.Draw(image)

        color = (35, 35, 35)


        left_x_offset = 15
        right_x_offset = 54

        d.line(
            [
                right_x_offset,
                0,
                right_x_offset,
                self._matrix.dimensions[1]
            ],
            fill=color
        )

        d.line(
            [
                left_x_offset,
                0,
                left_x_offset + 13,
                self._matrix.dimensions[1]
            ],
            fill=color
        )

    def draw_time(self, image, time):
        x_offset = 1
        y_offset = 1

        color = (170, 170, 170)

        font_path = os.path.join(Config.FONTS, "resolution-3x4.ttf")

        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        time_str = datetime.fromtimestamp(time).strftime("%I:%M %p")
        time_str = time_str.lstrip("0")

        text_size = d.textsize(time_str, f)
        x = self._matrix.dimensions[0] - text_size[0] - x_offset
        y = self._matrix.dimensions[1] - text_size[1] - y_offset

        d.text(
            (
                x, y
            ),
            time_str,
            font=f,
            fill=color
        )
