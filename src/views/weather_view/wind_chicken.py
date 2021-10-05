from PIL import Image, ImageDraw, ImageFont
import random

from config import FONTS

class WindChicken():
    BG_COLOR = "black"

    MIN_LENGTH = 2
    MAX_LENGTH = 4

    def __init__(self, matrix):
        self._matrix = matrix
        self._particles = []

        self.initialize_particles()

    def initialize_particles(self):
        for i in range(15):
            p = self.create_particle()
            self._particles.append(p)

    def create_particle(self, x_offset=0):
        x_variation = 3

        x = random.randint(x_offset, x_offset + x_variation)
        
        if x_offset == 0:
            x = random.randint(0, 64)

        y = random.randint(0, 32)
        x_offset = random.randint(4, 8)
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

    def generate_chicken_image(self):
        image = Image.new("RGB", self._matrix.dimensions, color=self.BG_COLOR)

        self.spawn_particles()
        self.update_particles()
        self.draw_particles(image)
        
        return image

    def spawn_particles(self):
        spawn_start = 64
        spawn_rate = 15

        for i in range(spawn_rate):
            if random.randint(0, spawn_rate) == 0:
                p = self.create_particle(x_offset=spawn_start)
                self._particles.append(p)
        

    def update_particles(self):
        for p in self._particles:
            p.x0 -= 4
            p.x1 -= 4

            if random.randint(0, 30) == 0:
                p.y0 += random.choice((-1, 1))

            if p.x1 <= 0:
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
                fill="white"
            )

class Particle:
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    