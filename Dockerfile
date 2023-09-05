#FROM jsavargas/telethon_downloader:ffmpeg AS basetelethon
FROM alpine AS basetelethon

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apk update && \
    apk upgrade 
RUN apk add --no-cache python3 py3-pip 
RUN apk add --no-cache ffmpeg
    #apk add --no-cache build-base && \
    #apk add --no-cache git && \
RUN pip install --upgrade pip 

#RUN pip install  -r requirements.txt
RUN pip install telethon
RUN pip install requests
RUN pip install yt-dlp
    #apk del build-base git && \
RUN rm -rf /tmp/* /var/cache/apk/*



FROM basetelethon

COPY telethon-downloader /app
#COPY root/ /

RUN chmod 777 /app/bottorrent.py 


VOLUME /download /watch /config

CMD ["python3", "/app/bottorrent.py"]
