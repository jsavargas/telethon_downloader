FROM jsavargas/telethon_downloader:41f0c15e4b



WORKDIR /app
COPY requirements.txt requirements.txt





COPY telethon-downloader /app
COPY root/ /

RUN chmod 777 /app/bottorrent.py
RUN chmod 777 -R /etc/services.d/



VOLUME /download /watch /config

