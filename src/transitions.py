from PIL import Image, ImageChops
import time

class Transitions:
    def vertical_transition(matrix, prev_image, new_image, unsafe=True):
        TRANSITION_INTERVAL = 10
        SHIFT_AMOUNT = 1

        image = Image.new("RGB", (matrix.dimensions[0], matrix.dimensions[1] * 2), color="black")
        image.paste(new_image, (0,0))
        image.paste(prev_image, (0, matrix.dimensions[1]))

        current_offset = 0

        # Handle the transition
        while True:
            image = ImageChops.offset(image, 0, SHIFT_AMOUNT)
            cropped = image.crop(
                (
                    0,
                    matrix.dimensions[1],
                    matrix.dimensions[0],
                    matrix.dimensions[1] * 2
                )
            )

            current_offset += SHIFT_AMOUNT

            if current_offset > matrix.dimensions[1]:
                break

            matrix.set_image(cropped, unsafe=unsafe)
            msleep(TRANSITION_INTERVAL)

def msleep(ms):
    """
    Sleep in milliseconds.
    """
    time.sleep(ms / 1000)