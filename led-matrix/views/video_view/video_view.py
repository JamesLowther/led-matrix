from PIL import Image
from common import msleep
from config import Config

import os
import json
import tarfile
import io

class VideoView:
    def __init__(self, matrix, press_event, video, loop=True):
        self._matrix = matrix
        self._press_event = press_event

        self._loop = loop

        self._video = video
        self._sleep = 100
        self._frames = []

        self._valid_data = self.load_video()

    def run(self):
        if not self._valid_data:
            return

        current_frame = 0
        while not self._press_event.is_set():
            self._matrix.set_image(self._frames[current_frame])
            msleep(self._sleep)

            if not self._loop and current_frame == (len(self._frames) - 1):
                return True

            current_frame = (current_frame + 1) % len(self._frames)

    def load_video(self):
        path = os.path.join(Config.ASSETS_PATH, "video_view", f"{self._video}.tar.gz")

        if not (os.path.exists(path) and tarfile.is_tarfile(path)):
            return False

        tar = tarfile.open(path, "r:gz")

        for member in tar:
            if "metadata.json" in member.name:
                meta_file = tar.extractfile(member)
                meta_data = json.load(meta_file)
                self._sleep = (1000 // meta_data["fps"])
                continue

            frame = tar.extractfile(member).read()
            self._frames.append(Image.open(io.BytesIO(frame)))

        return True
