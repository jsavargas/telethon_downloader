#FROM jsavargas/telethon_downloader:ffmpeg AS basetelethon
FROM python:3-slim AS basetelethon

RUN pip install -U cryptg telethon telethon[cryptg] 


FROM basetelethon

COPY telethon-downloader /app
#COPY root/ /

RUN chmod 777 /app/bottorrent.py


VOLUME /download /watch /config

CMD ["python3", "/app/bottorrent.py"]
