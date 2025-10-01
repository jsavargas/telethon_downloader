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




COPY src .

RUN chmod +x /app/app.py

VOLUME /download /watch /config

ENTRYPOINT ["python", "app.py"]

