FROM python

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get -qy dist-upgrade && \
    apt-get install -qy --no-install-recommends \
    ffmpeg \
    unzip && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install -r requirements.txt


WORKDIR /app


COPY telethon-downloader /app

RUN chmod +x /app/bottorrent.py

VOLUME /download /watch /config

CMD ["python3", "/app/bottorrent.py"]
