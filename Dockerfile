FROM ghcr.io/linuxserver/baseimage-ubuntu:focal



WORKDIR /app
COPY requirements.txt requirements.txt


RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	ffmpeg python3 python3-pip && \
	usermod -d /app abc
	
RUN	python3 -m pip install --upgrade pip 
RUN	pip3 install --upgrade --force-reinstall -r requirements.txt  


COPY telethon-downloader /app
COPY root/ /

RUN chmod 777 /app/bottorrent.py
RUN chmod 777 -R /etc/services.d/



VOLUME /download /watch /config

