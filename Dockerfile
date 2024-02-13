FROM ubuntu



RUN apt-get update && apt-get install -y --no-install-recommends \
                                python3 \
                                python3-dev \
                                python3-pip \
                                python3-setuptools \
                                python3-wheel \
                                build-essential \
                && rm -rf /var/lib/apt/lists/* 

RUN pip3 install cryptg 
RUN pip3 install telethon[cryptg]

RUN apt-get remove --purge -y build-essential \
                                python3-dev \
                && apt autoremove -y \
                && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENTRYPOINT ["/app/tg_downloader.py"]