FROM python

WORKDIR /app

COPY requirements.txt requirements.txt


RUN    apt-get -q update 
RUN    apt-get -qy dist-upgrade 
RUN    apt-get install -qy ffmpeg 
RUN    apt-get install -qy python3-pip 
RUN    apt-get install -qy unzip 
RUN    python3 -m pip install --upgrade pip  && \
    pip3 install --upgrade -r requirements.txt && \
    apt-get remove --purge -y build-essential  && \
    apt-get autoclean -y && apt-get autoremove -y  && \
    rm -rf /default /etc/default /tmp/* /etc/cont-init.d/* /var/lib/apt/lists/* /var/tmp/*




COPY telethon-downloader /app
#COPY root/ /

RUN chmod 777 /app/bottorrent.py


VOLUME /download /watch /config

CMD ["python3", "/app/bottorrent.py"]
