from PIL import Image, ImageDraw, ImageFont
import os

from config import Config

class MoonView:
    BG_COLOR = "black"

    def __init__(self, matrix):
        self._matrix = matrix
        self._moon_phase = None

    def update_moon(self, moon_data):
        if moon_data == 0 or moon_data == 1:
            self._moon_phase = {
                "id": 0,
                "offset": 4,
                "phase": "new moon"
            }
        elif 0 < moon_data < 0.25:
            self._moon_phase = {
                "id": 1,
                "offset": 2,
                "phase": "waxing crscnt"
            }
        elif moon_data == 0.25:
            self._moon_phase = {
                "id": 2,
                "offset": 2,
                "phase": "first quarter"
            }
        elif 0.25 < moon_data < 0.5:
            self._moon_phase = {
                "id": 3,
                "offset": 2,
                "phase": "waxing gibbous"
            }
        elif moon_data == 0.5:
            self._moon_phase = {
                "id": 4,
                "offset": 4,
                "phase": "full moon"
            }
        elif 0.5 < moon_data < 0.75:
            self._moon_phase = {
                "id": 5,
                "offset": 2,
                "phase": "waning gibbous"
            }
        elif moon_data == 0.75:
            self._moon_phase = {
                "id": 6,
                "offset": 2,
                "phase": "last quarter"
            }
        elif 0.75 < moon_data < 1:
            self._moon_phase = {
                "id": 7,
                "offset": 2,
                "phase": "waning crscnt"
            }

    def generate_moon_image(self):
        image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)

        image = self.draw_moon(image)
        self.draw_phase(image)

        return image

    def draw_phase(self, image):
        x_offset = -2
        y_offset = 10

        spacing = 2

        color = (170, 170, 170)

        font_path = os.path.join(Config.FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(image)

        phase = self._moon_phase["phase"]
        phase_s = phase.split(" ")

        top_str = phase_s[0]
        bottom_str = phase_s[1]

        top_size = d.textsize(top_str, f)
        bottom_size = d.textsize(bottom_str, f)

        d.text(
            (
                (self._matrix.dimensions[0] / 4) * 3 - (top_size[0] / 2) + x_offset,
                y_offset
            ),
            top_str,
            font=f,
            fill=color
        )

        d.text(
            (
                (self._matrix.dimensions[0] / 4) * 3 - (bottom_size[0] / 2) + x_offset, 
                y_offset + top_size[1] + spacing
            ),
            bottom_str,
            font=f,
            fill=color
        )

    def draw_moon(self, image):
        x_offset = self._moon_phase["offset"]
        y_offset = 4
        
        size = 24

        moon_id = self._moon_phase["id"]

        path = os.path.join(Config.SRC_BASE, "assets", "weatherview", "moon_icons", f"{moon_id}.png")
        image = Image.open(path)

        resized = image.resize((size, size), Image.BOX)

        image.paste(
            resized,
            (
                x_offset,
                y_offset
            )
        )

        return image
    
