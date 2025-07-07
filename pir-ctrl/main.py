from signal import pause
import subprocess
import logging

import gpiozero

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def motion_function():
    logger.info("Motion detected. Starting led-matrix.service...")
    subprocess.run(["systemctl", "start", "led-matrix.service"], check=True)
    logger.info("led-matrix.service started")


def no_motion_function():
    logger.info("Motion stopped. Stopping led-matrix.service...")
    subprocess.run(["systemctl", "stop", "led-matrix.service"], check=True)
    logger.info("led-matrix.service stopped")


def main():
    pir = gpiozero.MotionSensor(14)

    pir.when_motion = motion_function
    pir.when_no_motion = no_motion_function

    pause()


main()
