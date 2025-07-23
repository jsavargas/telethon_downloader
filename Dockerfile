FROM python

WORKDIR /app

COPY requirements.txt requirements.txt

#RUN apt-get update && apt-get -qy dist-upgrade && \
#    apt-get install -qy --no-install-recommends \
#    ffmpeg \
#    unzip && \
#    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt


COPY src .

VOLUME /download /watch /config

CMD ["python", "app.py"]

