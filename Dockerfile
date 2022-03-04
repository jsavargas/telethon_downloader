FROM jsavargas/telethon_downloader



WORKDIR /app
COPY requirements.txt requirements.txt

# install packages
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	ffmpeg && \
	usermod -d /app abc && \
	python3 -m pip install --upgrade pip && \
	pip3 install --upgrade --force-reinstall -r requirements.txt  && \
	apt-get remove --purge -y build-essential && \
	apt-get autoclean -y && apt-get autoremove -y && \
	rm -rf \
	/default/ \
	/etc/default/ \
	/tmp/* \
	/etc/cont-init.d/* \
	/var/lib/apt/lists/* \
	/var/tmp/* 




COPY telethon-downloader /app
COPY root/ /

RUN chmod 777 /app/bottorrent.py
RUN chmod 777 -R /etc/services.d/



VOLUME /download /watch /config

