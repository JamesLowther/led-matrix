import tkinter as tk
import PIL
from PIL import ImageTk, ImageDraw
import sys

class RGBMatrix:
    def __init__(self, options):
        self.width = options.cols
        self.height = options.rows

        self.__window = MatrixWindow()

    def SetImage(self, image):
        self.__window.update_image(image)

class RGBMatrixOptions:
    def __init__(self):
        self.rows = None
        self.cols = None
        self.chain_length = None
        self.row_address_type = None
        self.multiplexing = None
        self.pwm_bits = None
        self.brightness = None
        self.pwm_lsb_nanoseconds = None
        self.led_rgb_sequence = None
        self.pixel_mapper_config = None
        self.show_refresh_rate = None
        self.gpio_slowdown = None
        self.disable_hardware_pulsing = None
        self.hardware_mapping = None

class MatrixWindow():
    WIDTH = 1024
    HEIGHT = WIDTH // 2

    def __init__(self):
        self.__root = tk.Tk()
        self.__root.title("Virtual RGB Matrix")
        self.__root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.__root.protocol("WM_DELETE_WINDOW", self.handle_close)

        self.__canvas = tk.Canvas(self.__root, width=self.WIDTH, height=self.HEIGHT)
        self.__canvas.pack()

        self.__current_image = None
        self.__image_id = self.__canvas.create_image(0, 0, anchor=tk.NW)
        self.update_window()

    def update_image(self, image):
        resized_image = image.resize((int(self.__canvas["width"]), int(self.__canvas["height"])), resample=PIL.Image.BOX)
        grid_image = self.draw_grid(resized_image)
        tk_image = ImageTk.PhotoImage(grid_image)
        self.__current_image = tk_image
        self.__canvas.itemconfig(self.__image_id, image=self.__current_image)
        self.update_window()

    def draw_grid(self, image):
        pixel_w = int(self.__canvas["width"]) // 64
        pixel_h = int(self.__canvas["height"]) // 32
        
        line_w_horizontal = pixel_w // 3

        draw = ImageDraw.Draw(image)

        # Horizontal lines.
        for i in range(33):
            y = i * pixel_h
            draw.line([(0, y), (self.WIDTH, y)], fill="black", width=line_w_horizontal)

        # Vertical lines.
        for i in range(65):
            x = i * pixel_w
            draw.line([(x, 0), (x, self.HEIGHT)], fill="black", width=line_w_horizontal)
        
        return image

    def update_window(self):
        try:
            self.__root.update()
            self.__root.update_idletasks()
        except tk.TclError:
            sys.exit(0)

    def handle_close(self):
        self.__root.destroy()