from PIL import Image, ImageDraw, ImageFont
import time

class TestView():
    def __init__(self, matrix):
        self.matrix = matrix

    def run(self):
        base = time.time()
        while True:
            image = Image.new("RGB", self.matrix.dimensions, color="green")
            f = ImageFont.truetype("./assets/PixeloidSans.ttf", 9)
            # image.putpixel((63,31), (155,155,55))
            d = ImageDraw.Draw(image)
            d.text(
                (0, 0),
                str(time.time() - base),
                font=f,
                fill=(255, 255, 255)
            )

            self.matrix.set_image(image)

            # time.sleep(3)