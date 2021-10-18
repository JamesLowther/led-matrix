from PIL import Image, ImageFont, ImageDraw
from config import FONTS
import time
import os

class SwitchView:
    def __init__(self, matrix, press_event, long_press_event):
        self._matrix = matrix
        self._press_event = press_event
        self._long_press_event = long_press_event

    def show_mode(self, current_mode):
        new_mode = not current_mode

        while not self._long_press_event.is_set():
            new_mode = not new_mode

            x_offset = 0
            y_offset = 7
            y_spacing = 9

            image = Image.new("RGB", self._matrix.dimensions, color="black")

            font_path = os.path.join(FONTS, "6px-Normal.ttf")
            f = ImageFont.truetype(font_path, 8)
            d = ImageDraw.Draw(image)

            top_str = "Mode set to"
            top_color = (170, 170, 170)
            top_size = d.textsize(top_str, f)

            bottom_str = "MANUAL"
            bottom_color = "salmon"
            bottom_size = d.textsize(bottom_str, f)

            if new_mode:
                x_offset = 3
                bottom_str = "TIMED"
                bottom_color = "limegreen"

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

        return new_mode
