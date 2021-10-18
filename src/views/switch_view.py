from PIL import Image, ImageFont, ImageDraw
from config import Config
import time
import os

class SwitchView:
    COLORS = {
        "timed": "limegreen",
        "manual": "salmon"
    }

    def __init__(self, matrix, press_event, long_press_event):
        self._matrix = matrix
        self._press_event = press_event
        self._long_press_event = long_press_event

    def show_mode(self, current_mode, modes):
        new_mode_i = modes.index(current_mode)
        new_mode_i = (new_mode_i - 1) % len(modes)

        while not self._long_press_event.is_set():
            new_mode_i = (new_mode_i + 1) % len(modes)

            x_offset = 0
            y_offset = 7
            y_spacing = 9

            image = Image.new("RGB", self._matrix.dimensions, color="black")

            font_path = os.path.join(Config.FONTS, "6px-Normal.ttf")
            f = ImageFont.truetype(font_path, 8)
            d = ImageDraw.Draw(image)

            top_str = "Mode set to"
            top_color = (170, 170, 170)
            top_size = d.textsize(top_str, f)

            bottom_str = modes[new_mode_i].upper()

            bottom_color = None
            try:
                bottom_color = self.COLORS[modes[new_mode_i]]
            except KeyError:
                bottom_color = "DarkViolet"

            bottom_size = d.textsize(bottom_str, f)

            d.text(
                [
                    (self._matrix.dimensions[0] / 2) - (top_size[0] / 2),
                    y_offset
                ],
                top_str,
                font=f,
                fill=top_color
            )

            d.text(
                [
                    (self._matrix.dimensions[0] / 2) - (bottom_size[0] / 2) + x_offset,
                    y_offset + y_spacing
                ],
                bottom_str,
                font=f,
                fill=bottom_color
            )

            self._matrix.set_image(image)

            self._press_event.wait()
            self._press_event.clear()
            
        self._long_press_event.clear()

        return modes[new_mode_i]
