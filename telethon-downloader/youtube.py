from yt_dlp import YoutubeDL

import logger
import constants
import asyncio


class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'progress_hooks': [self.progress_hook],
            'format': constants.YOUTUBE_FORMAT, 
            'outtmpl': f'{constants.PATH_YOUTUBE}/%(title)s.%(ext)s',
            'cachedir':'False', 
            "retries": 10, 
            'merge_output_format':'mkv' 
            }

    def progress_hook(self, data):
        if data['status'] == 'downloading':
            percent = data['_percent_str']
            logger.logger.info(f"Descargando: {percent}")

    async def download(self, url):
        with YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([url])
