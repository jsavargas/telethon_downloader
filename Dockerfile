FROM ghcr.io/linuxserver/baseimage-ubuntu:bionic


WORKDIR /app


COPY requirements.txt requirements.txt

# install packages
RUN apt-get update && \
 apt-get install -y --no-install-recommends \
	python3 \
	python3-dev \
	python3-pip \
	python3-setuptools \
	python3-wheel \
	build-essential && \
	python3 -m pip install --upgrade pip && \
	pip3 install -r requirements.txt  && \
	apt-get remove --purge -y build-essential && \
 apt-get autoclean -y && apt-get autoremove -y && \
 rm -rf \
	/config/ \
	/default/ \
	/etc/default/ \
	/tmp/* \
	/etc/cont-init.d/* \
	/var/lib/apt/lists/* \
	/var/tmp/* 





COPY telethon-downloader /app

RUN chmod 777 /app/bottorrent.py


VOLUME /download /watch /config

CMD ["python3", "/app/bottorrent.py"]

