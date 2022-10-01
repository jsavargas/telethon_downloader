FROM ghcr.io/linuxserver/baseimage-ubuntu:bionic AS basetelethon



WORKDIR /app

RUN apt-get update && apt-get upgrade -y 

COPY requirements.txt requirements.txt

RUN	apt-get install -y \
	ffmpeg \
	python3 \
	python3-setuptools \
	python3-pip && \
	usermod -d /app abc && \
	python3 -m pip install --upgrade pip && \
	pip3 install -r requirements.txt  && \
	apt-get remove --purge -y build-essential && \
	apt-get autoclean -y && apt-get autoremove -y && \
	rm -rf /config /default /etc/default /tmp/* /etc/cont-init.d/* /var/lib/apt/lists/* /var/tmp/* 



FROM basetelethon

COPY telethon-downloader /app
COPY root/ /

RUN chmod 777 /app/bottorrent.py
RUN chmod 777 -R /etc/services.d/


VOLUME /download /watch /config

