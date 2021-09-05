import PIL

class RGBMatrix:
    def __init__(self, options):
        self.width = options.cols
        self.height = options.rows

    def SetImage(self, image):
        print(image)
        image.show()

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