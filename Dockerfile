FROM linuxserver/ffmpeg:latest

WORKDIR /app

COPY requirements.txt requirements.txt

#RUN apt-get update && apt-get -qy dist-upgrade && \
#    apt-get install -qy --no-install-recommends \
#    ffmpeg \
#    unzip && \
#    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -qy python3 python3-pip python3-venv

# Crear y activar venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt


COPY src .

VOLUME /download /watch /config

ENTRYPOINT ["python", "app.py"]

