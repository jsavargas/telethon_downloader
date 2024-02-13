#FROM jsavargas/telethon_downloader:ffmpeg AS basetelethon
FROM ubuntu AS basetelethon

RUN apt-get update && \
 apt-get install -y --no-install-recommends \
	ncdu \
	python3 \
	python3-dev \
	python3-pip \
	python3-setuptools \
	python3-wheel \
	build-essential

RUN pip install -U cryptg telethon 


FROM basetelethon

COPY telethon-downloader /app
#COPY root/ /

RUN chmod 777 /app/bottorrent.py


VOLUME /download /watch /config

CMD ["python3", "/app/bottorrent.py"]
