FROM jsavargas/telethon_downloader:ffmpeg AS basetelethon

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apk update && \
    apk upgrade && \
    #apk add --no-cache ffmpeg && \
    #apk add --no-cache build-base && \
    #apk add --no-cache git && \
    pip install --upgrade pip && \
    pip install -r requirements.txt --upgrade && \
    apk del build-base git && \
    rm -rf /tmp/* /var/cache/apk/*



FROM basetelethon

COPY telethon-downloader /app
COPY root/ /

RUN chmod 777 /app/bottorrent.py && chmod 777 -R /etc/services.d/


VOLUME /download /watch /config

CMD ["python3", "/app/bottorrent.py"]
