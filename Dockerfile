FROM python


RUN apt-get update && apt-get install python3-pip -qy 

RUN pip3 install --upgrade setuptools
RUN pip3 install telethon
RUN pip3 install telethon-cryptg
RUN pip3 install cryptg


WORKDIR /app
ENTRYPOINT ["/app/tg_downloader.py"]