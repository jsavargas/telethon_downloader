FROM python:3-slim


MAINTAINER Basado en el contenedor de rodriguezst <github.com/rodriguezst> rodriguezst/telethon_downloader



RUN pip install -U cryptg telethon[cryptg] 


COPY tg_downloader.py /app/tg_downloader.py



RUN chown -R 99:100 /app
RUN chmod +x /app/tg_downloader.py 


USER 99:100 
 
WORKDIR /app
ENTRYPOINT ["/app/tg_downloader.py"]
