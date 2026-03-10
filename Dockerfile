FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apk add --no-cache \
    ffmpeg \
    unzip && \
    python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

COPY src .

RUN chmod +x /app/app.py

VOLUME /download /watch /config

ENTRYPOINT ["python", "app.py"]