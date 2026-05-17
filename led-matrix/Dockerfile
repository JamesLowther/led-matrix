################################################################
# Builder
################################################################
FROM debian:trixie-slim AS builder

ENV PYTHONUNBUFFERED=1

RUN apt-get update -y \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        git \
        build-essential \
        python3-venv \
        python3-pip \
        python3-dev \
        python-dev-is-python3 \
        python3-pil \
        cython3 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV VIRTUAL_ENV="/opt/venv"
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools

WORKDIR /build

RUN pip install --no-cache-dir git+https://github.com/hzeller/rpi-rgb-led-matrix

COPY requirements.txt requirements-pi.txt ./
RUN pip install --no-cache-dir -r ./requirements-pi.txt

################################################################
# Runtime
################################################################
FROM debian:trixie-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV="/opt/venv"

ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

RUN apt-get update -y \
    && DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
         python3 \
         python-dev-is-python3 \
         cython3 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 app \
    && useradd -g 1000 -u 1000 -s /usr/sbin/nologin -d /app app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY ./src ./src

CMD [ \
    "python3", \
    "./src/main.py", \
    "--led-drop-privs-user=app", \
    "--led-drop-privs-group=app", \
    "--led-slowdown-gpio=2", \
    "--led-brightness=85", \
    "--led-gpio-mapping=adafruit-hat-pwm" \
]
