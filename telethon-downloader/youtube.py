from yt_dlp import YoutubeDL

import os
import time
import asyncio

import logger
import constants

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

    async def downloadVideo(self, url, message):
        with YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info_dict)
            total_downloads = 1
            youtube_path = constants.PATH_YOUTUBE
            if '_type' in info_dict and info_dict["_type"] == 'playlist':
                total_downloads = len(info_dict['entries'])
                youtube_path = os.path.join(constants.PATH_YOUTUBE,info_dict['uploader'], info_dict['title'])
            else:
                youtube_path = os.path.join(constants.PATH_YOUTUBE,info_dict['uploader'])

            ydl_opts = { 'format': constants.YOUTUBE_FORMAT, 'outtmpl': f'{youtube_path}/%(title)s.%(ext)s','cachedir':'False','ignoreerrors': True, "retries": 10, 'merge_output_format':'mkv' }
            ydl_opts.update(ydl_opts)

        with YoutubeDL(ydl_opts) as ydl:
            logger.logger.info(f'DOWNLOADING VIDEO YOUTUBE [{url}] [{file_name}]')
            await message.edit(f'downloading {total_downloads} videos...')
            res_youtube = ydl.download([url])

            if (res_youtube == False):
                os.chmod(youtube_path, 0o777)
                filename = os.path.basename(file_name)
                logger.logger.info(f'DOWNLOADED {total_downloads} VIDEO YOUTUBE [{file_name}] [{youtube_path}][{filename}]')
                end_time_short = time.strftime('%H:%M', time.localtime())
                await message.edit(f'Downloading finished {total_downloads} video at {end_time_short}\n{youtube_path}')
            else:
                logger.logger.info(f'ERROR: ONE OR MORE YOUTUBE VIDEOS NOT DOWNLOADED [{total_downloads}] [{url}] [{youtube_path}]')
                await message.edit(f'ERROR: one or more videos not downloaded') 

    async def downloadAudio(self, url, message):
        logger.logger.info(f'downloadAudio [{url}] [{message}]')
        
        os.makedirs(constants.YOUTUBE_AUDIOS_FOLDER, exist_ok=True)
        youtube_path = os.path.join(constants.YOUTUBE_AUDIOS_FOLDER)

        ydl_opts = {
            'format': 'bestaudio/best',  # Descargar la mejor calidad de audio disponible
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',  # Extraer el audio
                'preferredcodec': 'mp3',       # Formato de salida del audio (por ejemplo, mp3)
                'preferredquality': '320',     # Calidad del audio (bitrate en kbps)
            }],
            'outtmpl': os.path.join(youtube_path, '%(title)s.%(ext)s')
        }

        with YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            #logger.logger.info(f'downloadAudio info_dict: [{info_dict}]')
            total_downloads = 1
            if '_type' in info_dict and info_dict["_type"] == 'playlist':
                total_downloads = len(info_dict['entries'])
                await message.edit(f'finding {total_downloads} audios...')
        logger.logger.info(f'downloadAudio total_downloads: [{total_downloads}]')

        with YoutubeDL(ydl_opts) as ydl:
            await message.edit(f'downloading {total_downloads} audios...')
            res_youtube = ydl.download([url])

            if (res_youtube == False):
                os.chmod(constants.YOUTUBE_AUDIOS_FOLDER, 0o777)
                end_time_short = time.strftime('%H:%M', time.localtime())
                await message.edit(f'Downloading finished {total_downloads} audio at {end_time_short}\n{youtube_path}')

