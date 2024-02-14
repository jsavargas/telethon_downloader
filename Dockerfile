FROM python:3.9-alpine




RUN pip install --no-cache-dir cryptg

WORKDIR /app
ENTRYPOINT ["/app/tg_downloader.py"]