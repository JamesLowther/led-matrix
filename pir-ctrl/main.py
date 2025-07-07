from signal import pause
import subprocess
import logging
import time

import gpiozero

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SERVICE_ATTEMPTS = 3


def motion_function():
    logger.info("Motion detected. Starting led-matrix.service...")

    for i in range(SERVICE_ATTEMPTS):
        try:
            subprocess.run(["systemctl", "start", "led-matrix.service"], check=True)
            break

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start service: {e}")

        time.sleep(3)

    logger.info("led-matrix.service started")


def no_motion_function():
    logger.info("Motion stopped. Stopping led-matrix.service...")

    for i in range(SERVICE_ATTEMPTS):
        try:
            subprocess.run(["systemctl", "stop", "led-matrix.service"], check=True)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop service: {e}")

        time.sleep(3)

    logger.info("led-matrix.service stopped")


def main():
    pir = gpiozero.MotionSensor(14)

    pir.when_motion = motion_function
    pir.when_no_motion = no_motion_function

    pause()


if __name__ == "__main__":
    main()
