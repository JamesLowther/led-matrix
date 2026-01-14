################################################################
# Build
################################################################
FROM debian:trixie-slim AS builder

ENV PYTHONUNBUFFERED=1

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update \
    && apt-get -y install git build-essential cython3 python3-dev python3-venv python3-pip python3-pil

RUN git clone https://github.com/hzeller/rpi-rgb-led-matrix.git /opt/rpi-rgb-led-matrix

RUN python3 -m venv /opt/venv

ENV VIRTUAL_ENV="/opt/venv"
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

RUN pip install setuptools

WORKDIR /opt/rpi-rgb-led-matrix

RUN make build-python HARDWARE_DESC=adafruit-hat-pwm \
    && make install-python HARDWARE_DESC=adafruit-hat-pwm

COPY requirements.txt requirements-pi.txt .
RUN pip install --no-cache-dir -r ./requirements-pi.txt

################################################################
# Runtime
################################################################
FROM debian:trixie-slim AS runtime

COPY --from=builder /opt/venv /opt/venv

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV VIRTUAL_ENV="/opt/venv"
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

RUN apt-get -y update \
    && apt-get -y install python3

RUN groupadd -g 1000 app && useradd -g 1000 -u 1000 -s /usr/sbin/nologin -d /app app

WORKDIR /app

COPY ./src ./src

CMD ["python3", "./src/main.py", "--led-drop-privs-user=app", "--led-drop-privs-group=app", "--led-slowdown-gpio=2", "--led-brightness=85"]
