import os
from datetime import datetime

from PIL import Image, ImageFont, ImageDraw
from config import SRC_BASE, FONTS

class TemperatureView():
    BG_COLOR = "black"

    def __init__(self, matrix, location):
        self._matrix = matrix
        self._location = location

    def generate_temperature_image(self, weather_data):

        self._weather_data = weather_data
        self._temperature_image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)

        self.draw_location_text()
        self.draw_current_temp()
        self.draw_forecast()

        return self._temperature_image

    def draw_location_text(self):
        font_path = os.path.join(FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(self._temperature_image)

        x_offset = 2
        y_offset = 2

        color = (170, 170, 170)

        d.text(
            (x_offset, y_offset),
            self._location,
            font=f,
            fill=color
        )

    def draw_current_temp(self):
        font_path = os.path.join(FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(self._temperature_image)

        x_offset = 2
        y_offset = 3

        radius = 1

        color = (170, 170, 170)

        data = self._weather_data[self._location]["current"]

        current_temp = str(int(data["feels_like"] - 273.15))

        size = d.textsize(current_temp, f)

        d.text(
            (
                self._matrix.dimensions[0] - size[0] - x_offset - radius - 1,
                y_offset
            ),
            current_temp,
            font=f,
            fill=color
        )

        d.rectangle(
            [
                self._matrix.dimensions[0] - radius - x_offset - 1,
                y_offset - 1,
                self._matrix.dimensions[0] - x_offset - 1,
                y_offset + radius - 1
            ],
            fill=color
        )

        icon = self.get_icon(data["weather"][0]["icon"], 7)

        self._temperature_image.paste(
            icon, 
            (
                self._matrix.dimensions[0] - size[0] - x_offset - icon.width - radius - 3, 
                y_offset - 2
            )
        )
        
    def draw_forecast(self):
        font_path = os.path.join(FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(self._temperature_image)
        
        data = self._weather_data[self._location]["daily"]

        x_offset = 1
        y_offset = 10

        neutral_color = (170, 170, 170)

        hot_color = "firebrick"
        warm_color = "peru"
        cold_color = "lightblue"
        freezing_color = "cadetblue"

        hot = 20
        freezing = -20

        block_width = 9
        icon_size= 4

        x = x_offset

        for i, forecast in enumerate(data):
            
            day = datetime.fromtimestamp(forecast["dt"]).strftime("%A")[0]
            day_size = d.textsize(day, f)

            day_x = x + (block_width // 2) - (day_size[0] // 2)
            day_y = y_offset

            d.text(
                (
                    day_x,
                    day_y
                ),
                day,
                font=f,
                fill=neutral_color
            )

            min_temp_int = int(forecast["temp"]["min"] - 273.15)
            max_temp_int = int(forecast["temp"]["max"] - 273.15)

            min_color = neutral_color
            if min_temp_int > 0:
                if min_temp_int >= hot:
                    min_color = hot_color
                else:
                    min_color = warm_color
            elif min_temp_int <= 0:
                if min_temp_int <= freezing:
                    min_color = freezing_color
                else:
                    min_color = cold_color
                min_temp_int = abs(min_temp_int)

            max_color = neutral_color
            if max_temp_int > 0:
                if max_temp_int >= hot:
                    max_color = hot_color
                else:
                    max_color = warm_color
            elif max_temp_int < 0:
                if max_temp_int <= freezing:
                    max_color = freezing_color
                else:
                    max_color = cold_color
                max_temp_int = abs(max_temp_int)

            min_temp = str(min_temp_int)
            max_temp = str(max_temp_int)

            min_temp_size = d.textsize(min_temp, f)
            max_temp_size = d.textsize(max_temp, f)

            max_x = x + (block_width // 2) - (max_temp_size[0] // 2)
            max_y = y_offset + day_size[1]

            d.text(
                (
                    max_x,
                    max_y
                ),
                max_temp,
                font=f,
                fill=max_color
            )

            min_x = x + (block_width // 2) - (min_temp_size[0] // 2)
            min_y = y_offset + day_size[1] + max_temp_size[1]

            d.text(
                (
                    min_x,
                    min_y
                ),
                min_temp,
                font=f,
                fill=min_color
            )

            icon_x = x + (block_width // 2) - (icon_size // 2)
            icon_y = y_offset + day_size[1] + max_temp_size[1] + min_temp_size[1] + 2

            icon = self.get_icon(forecast["weather"][0]["icon"], icon_size)
            self._temperature_image.paste(
                icon, 
                (
                    icon_x, 
                    icon_y
                )
            )

            x += block_width

    def get_icon(self, code, size):
        path = os.path.join(SRC_BASE, "assets", "weatherview", "icons", f"{code}.png")
        image = Image.open(path)

        resized = image.resize((size, size), Image.BOX)

        return resized