from signal import pause
import docker
import logging
import time

import gpiozero

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ATTEMPTS = 3

client = docker.from_env()

def motion_function():
    logger.info("Motion detected. Starting led-matrix...")

    container = client.containers.get("led-matrix")
    container.start()

    logger.info("led-matrix started")


def no_motion_function():
    logger.info("Motion stopped. Stopping led-matrix...")

    container = client.containers.get("led-matrix")
    container.stop()

    logger.info("led-matrix stopped")


def main():
    logger.info("PIR Control started. Waiting for motion...")

    pir = gpiozero.MotionSensor(14)

    pir.when_motion = motion_function
    pir.when_no_motion = no_motion_function

    pause()


if __name__ == "__main__":
    main()
