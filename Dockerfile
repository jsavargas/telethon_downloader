FROM python:3.14-alpine AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apk add --no-cache gcc musl-dev libffi-dev python3-dev && \
    python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.14-alpine

WORKDIR /app

RUN apk add --no-cache ffmpeg unzip

COPY --from=builder /install /usr/local

COPY src .

RUN chmod +x /app/app.py

VOLUME /download /watch /config

ENTRYPOINT ["python", "app.py"]
