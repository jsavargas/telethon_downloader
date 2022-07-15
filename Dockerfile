FROM jsavargas/telethon_downloader:41f0c15e4b



WORKDIR /app
COPY requirements.txt requirements.txt


RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	ffmpeg python3 python3-pip


COPY telethon-downloader /app
COPY root/ /

RUN chmod 777 /app/bottorrent.py
RUN chmod 777 -R /etc/services.d/



VOLUME /download /watch /config

