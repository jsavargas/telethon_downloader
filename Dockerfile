FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apk add --no-cache \
    ffmpeg \
    unzip && \
    python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

COPY src .

RUN chmod +x /app/app.py && \
    addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

VOLUME /download /watch /config

USER appuser

ENTRYPOINT ["python", "app.py"]