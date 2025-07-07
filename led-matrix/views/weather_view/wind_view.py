from PIL import Image, ImageDraw, ImageFont
import random
import math
import os
import time

from config import Config

class WindView:
    BG_COLOR = "black"
    WIND_COLOR = (200, 200, 200)

    MIN_LENGTH = 4
    MAX_LENGTH = 8

    SPAWN_RATE = 2500

    MIN_WINDSPEED = 10
    MAX_WINDSPEED = 100

    def __init__(self, matrix):
        self._matrix = matrix
        self._particles = []

    def initialize_particles(self, windspeed):
        self.update_windspeed(windspeed)

        self._particles.clear()

        for i in range(int(0.3 * 100 * self._windspeed / self.MAX_WINDSPEED)):
            p = self.create_particle()
            self._particles.append(p)

    def update_windspeed(self, windspeed):
        self._display_windspeed = windspeed * 3.6
        windspeed = windspeed * 3.6
        self._windspeed = max(windspeed, self.MIN_WINDSPEED)
        self._windspeed = min(self._windspeed, self.MAX_WINDSPEED)

    def create_particle(self, x_offset=0):
        x_variation = 4

        x = random.randint(x_offset, x_offset + x_variation)

        if x_offset == 0:
            x = random.randint(24, 64)

        y = random.randint(0, 32)
        x_offset = random.randint(self.MIN_LENGTH, self.MAX_LENGTH)

        y_offset = 0
        if random.randint(0, 10) == 0:
                y_offset += random.choice((-1, 1))

        p = Particle(
            x,
            y,
            x + x_offset,
            y + y_offset
        )

        return p

    def generate_wind_image(self):
        image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)

        self.spawn_particles()
        self.update_particles()
        self.draw_particles(image)
        self.draw_time(image)
        self.draw_windspeed(image)
        return image

    def spawn_particles(self):
        spawn_rate = int(self.SPAWN_RATE / self._windspeed)

        spawn_start = self._matrix.dimensions[0]
        for i in range(16):
            if random.randint(0, spawn_rate) == 0:
                p = self.create_particle(x_offset=spawn_start)
                self._particles.append(p)

    def update_particles(self):
        x_change = 1 * (self._windspeed * 4) / self.MAX_WINDSPEED

        for p in self._particles:
            p.x0 -= x_change
            p.x1 -= x_change

            if random.randint(0, int(4000 / self._windspeed)) == 0:
                y_move = 1
                p.y0 += y_move
                p.y1 += y_move

            if p.x1 <= -115:
                self._particles.remove(p)

    def draw_particles(self, image):
        d = ImageDraw.Draw(image)
        for p in self._particles:
            d.line(
                [
                    p.x0,
                    p.y0,
                    p.x1,
                    p.y1,
                ],
                fill=self.WIND_COLOR
            )

    def draw_time(self, image):
        font_path = os.path.join(Config.FONTS, "cg-pixel-4x5.ttf")
        f = ImageFont.truetype(font_path, 5)
        d = ImageDraw.Draw(image)

        y_offset = 1

        time_str = time.strftime("%I:%M %p")
        time_str = time_str.lstrip("0")
        time_size = d.textsize(time_str, f)

        x = (self._matrix.dimensions[0] // 2) - (time_size[0] // 2)

        d.rectangle(
            [
                x,
                0,
                x + time_size[0],
                y_offset * 2 + time_size[1]
            ],
            fill = self.BG_COLOR
        )

        d.text(
            (
                x,
                y_offset
            ),
            time_str,
            font=f,
            fill=(170, 170, 170)
        )

    def draw_windspeed(self, image):
        font_path = os.path.join(Config.FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        y_offset = 1

        speed_str = f"{round(self._display_windspeed, 1)} km/h"
        speed_size = d.textsize(speed_str, f)

        x = (self._matrix.dimensions[0] // 2) - (speed_size[0] // 2)


        d.rectangle(
            [
                x,
                self._matrix.dimensions[1] - speed_size[1] - y_offset,
                x + speed_size[0],
                self._matrix.dimensions[1] - y_offset
            ],
            fill = self.BG_COLOR
        )

        d.text(
            (
                x,
                self._matrix.dimensions[1] - speed_size[1] - y_offset,
            ),
            speed_str,
            font=f,
            fill=(170, 170, 170)
        )

class Particle:
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
