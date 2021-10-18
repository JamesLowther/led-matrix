from PIL import ImageDraw, ImageFont
from config import Config

import os

class TrafficGraph:

    def draw_tx_rx(image, health_data):
        tx_color = "goldenrod"
        rx_color = "crimson"
        
        x_offset = 1
        y_offset = 18

        y_spacing = 0

        font_path = os.path.join(Config.FONTS, "resolution-3x4.ttf")
        f = ImageFont.truetype(font_path, 4)
        d = ImageDraw.Draw(image)

        wan_data = health_data[1]

        tx = round(wan_data["tx_bytes-r"] / 125000, 1)
        rx = round(wan_data["rx_bytes-r"] / 125000, 1)

        tx_str = str(tx) + " TX"
        rx_str = str(rx) + " RX"

        if len(tx_str) <= 6 and len(rx_str) <= 6:
            x_offset = 1

        tx_size = d.textsize(tx_str, f)
        rx_size = d.textsize(rx_str, f)

        d.text(
            [
                64 - tx_size[0] - x_offset,
                y_offset
            ],
            tx_str,
            font=f,
            fill=tx_color
        )

        d.text(
            [
                64 - rx_size[0] - x_offset,
                y_offset + tx_size[1] + y_spacing
            ],
            rx_str,
            font=f,
            fill=rx_color
        )

    def draw_graph(image, traffic_data):
        x_offset = 2
        y_offset = 20
        
        width = 35
        height = 8

        tx_color = "goldenrod"
        rx_color = "crimson"

        max_tx = float("-inf")
        max_rx = float("-inf")

        min_tx = float("inf")
        min_rx = float("inf")

        for x in traffic_data:
            max_tx = max(max_tx, x["wan-tx_bytes"])
            max_rx = max(max_rx, x["wan-rx_bytes"])
            min_tx = min(min_tx, x["wan-tx_bytes"])
            min_rx = min(min_rx, x["wan-rx_bytes"])

        d = ImageDraw.Draw(image)

        tx_prev = None
        rx_prev = None

        step = width / (len(traffic_data) - 1)

        max_tx_normal = max_tx - min_tx
        max_rx_normal = max_rx - min_rx

        # Draw graph lines.
        for i in range(len(traffic_data)):
            tx_x = x_offset + (step * i)
            tx_y = y_offset + height - (((traffic_data[i]["wan-tx_bytes"] - min_tx) / max_tx_normal) * height)

            rx_x = x_offset + (step * i)
            rx_y = y_offset + height - (((traffic_data[i]["wan-rx_bytes"] - min_rx) / max_rx_normal) * height)

            if i != 0:
                d.line(
                    [
                        tx_x, tx_y,
                        tx_prev[0], tx_prev[1]
                    ],
                    fill=tx_color
                )

                d.line(
                    [
                        rx_x, rx_y,
                        rx_prev[0], rx_prev[1]
                    ],
                    fill=rx_color
                )
        
            tx_prev = (tx_x, tx_y)
            rx_prev = (rx_x, rx_y)