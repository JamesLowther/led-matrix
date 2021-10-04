from PIL import Image, ImageFont, ImageDraw
import time

class PoweroffView():
    COUNTDOWN = 8

    def __init__(self, matrix, press_event):
        self._matrix = matrix
        self._press_event = press_event

    def start_shutdown(self):
        """
        Displays the shutdown dialog and checks to see if a cancel event occurs.
        Returns True if the system should shutdown and False otherwise.
        """
        x_offset = 3
        y_offset = 2

        spacing = 8

        spacing_2 = 12

        for i in range(self.COUNTDOWN, 0, -1):
            image = Image.new("RGB", self._matrix.dimensions, color="black")
            f = ImageFont.truetype("./src/assets/fonts/6px-Normal.ttf", 8)
            d = ImageDraw.Draw(image)

            d.text(
                (x_offset, y_offset),
                "Shutting down in",
                font=f,
                fill=(170, 170, 170)
            )

            d.text(
                (x_offset + 10, y_offset + spacing),
                f"{i} second(s)",
                font=f,
                fill=(170, 170, 170)
            )

            d.text(
                (x_offset + 1, y_offset + spacing + spacing_2),
                f"Press to cancel",
                font=f,
                fill=(184, 134, 11)
            )

            self._matrix.set_image(image)

            time.sleep(1)

            if self._press_event.is_set():
                return False

        return True

            


