from PIL import Image, ImageFont, ImageDraw
import time
import os
from config import Config


class PoweroffView:
    COUNTDOWN = 15

    def __init__(self, matrix, press_event, long_press_event):
        self._matrix = matrix
        self._press_event = press_event
        self._long_press_event = long_press_event

    def start_shutdown(self):
        """
        Displays the shutdown dialog and checks to see if a cancel event occurs.
        Returns True if the system should shutdown and False otherwise.
        """
        y_offset = 2

        spacing = 8

        spacing_2 = 12

        for i in range(self.COUNTDOWN, 0, -1):
            image = Image.new("RGB", self._matrix.dimensions, color="black")

            font_path = os.path.join(Config.FONTS, "6px-Normal.ttf")
            f = ImageFont.truetype(font_path, 8)
            d = ImageDraw.Draw(image)

            text_1_str = "Shutting down in"
            text_1_size = d.textsize(text_1_str, f)

            d.text(
                ((self._matrix.dimensions[0] / 2) - (text_1_size[0] / 2), y_offset),
                text_1_str,
                font=f,
                fill=(170, 170, 170),
            )

            if i == 1:
                text_2_str = f"{i} second"
            else:
                text_2_str = f"{i} seconds"

            text_2_size = d.textsize(text_2_str, f)

            d.text(
                (
                    (self._matrix.dimensions[0] / 2) - (text_2_size[0] / 2),
                    y_offset + spacing,
                ),
                text_2_str,
                font=f,
                fill=(170, 170, 170),
            )

            text_3_str = "PRESS TO CANCEL"
            text_3_size = d.textsize(text_3_str, f)

            d.text(
                (
                    (self._matrix.dimensions[0] / 2) - (text_3_size[0] / 2),
                    y_offset + spacing + spacing_2,
                ),
                text_3_str,
                font=f,
                fill=(184, 134, 11),
            )

            self._matrix.set_image(image)

            time.sleep(1)

            if self._long_press_event.is_set():
                return "switch_mode"

            if self._press_event.is_set():
                return False

        return True
