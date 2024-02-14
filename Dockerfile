FROM python


RUN apt-get update && apt-get install python3-pip -qy

RUN pip3 install telethon


WORKDIR /app
ENTRYPOINT ["/app/tg_downloader.py"]