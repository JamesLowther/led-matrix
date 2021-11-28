from PIL import Image
from common import msleep
from config import Config

import os
import json

class VideoView():
    def __init__(self, matrix, press_event, video):
        self._matrix = matrix
        self._press_event = press_event

        self._video = video
        self._sleep = 100
        self._frames = []

        self.load_video()

    def run(self):
        current_frame = 0
        while not self._press_event.is_set():
            self._matrix.set_image(self._frames[current_frame])
            current_frame = (current_frame + 1) % len(self._frames)
            msleep(self._sleep)

    def load_video(self):
        path = os.path.join(Config.ASSETS_PATH, "video_view", self._video)
        if os.path.exists(path):
            files = os.listdir(path)
            files.sort()
            for frame_name in files:
                if frame_name == "metadata.json":
                    continue

                frame_path = os.path.join(path, frame_name)
                self._frames.append(Image.open(frame_path))

        meta_path = os.path.join(path, "metadata.json")
        
        try:
            with open(meta_path, "r") as meta_file:
                meta_data = json.load(meta_file)
                meta_file.close()

                self._sleep = 1000 / meta_data["fps"]

        except FileNotFoundError:
            pass
