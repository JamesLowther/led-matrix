FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

################################################################
# Install rpi-rgb-led-matrix
################################################################
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update \
    && apt-get -y install make git build-essential python3-dev cython3

RUN git clone https://github.com/hzeller/rpi-rgb-led-matrix.git /opt/rpi-rgb-led-matrix

WORKDIR /opt/rpi-rgb-led-matrix

RUN make build-python \
    && make install-python HARDWARE_DESC=adafruit-hat-pwm

################################################################
# led-matrix
################################################################
WORKDIR /app

COPY requirements.txt requirements-pi.txt .
RUN pip install -r ./requirements-pi.txt

COPY ./src ./src

CMD ["python3", "./src/main.py", "--led-no-drop-privs", "--led-slowdown-gpio=2", "--led-brightness=85"]
