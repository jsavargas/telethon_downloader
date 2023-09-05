from yt_dlp import YoutubeDL

import os
import time
import asyncio

import logger
from constants import EnvironmentReader

class YouTubeDownloader:
    def __init__(self):
        self.constants = EnvironmentReader()
        self.ydl_opts = {
            'format': self.constants.get_variable("YOUTUBE_FORMAT_VIDEO"), 
            'outtmpl': f'{self.constants.get_variable("PATH_YOUTUBE")}/%(title)s.%(ext)s',
            'cachedir':'False', 
            "retries": 10, 
            'merge_output_format':'mkv',
            'progress_hooks': [self.progress_hook]
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
            youtube_path = self.constants.get_variable("PATH_YOUTUBE")
            self.change_permissions(youtube_path)

            if '_type' in info_dict and info_dict["_type"] == 'playlist':
                total_downloads = len(info_dict['entries'])
                youtube_path = os.path.join(self.constants.get_variable("PATH_YOUTUBE"),info_dict['uploader'], info_dict['title'])
            else:
                youtube_path = os.path.join(self.constants.get_variable("PATH_YOUTUBE"),info_dict['uploader'])

            ydl_opts = { 
                'format': self.constants.get_variable("YOUTUBE_FORMAT_VIDEO"),  
                'outtmpl': f'{youtube_path}/%(title)s.%(ext)s',
                'cachedir':'False',
                'ignoreerrors': True, 
                'retries': 10, 
                'merge_output_format':'mkv'
            }
            ydl_opts.update(ydl_opts)

        with YoutubeDL(ydl_opts) as ydl:
            logger.logger.info(f'DOWNLOADING VIDEO YOUTUBE [{url}] [{file_name}]')
            await message.edit(f'downloading {total_downloads} videos...')
            res_youtube = ydl.download([url])

            filename = os.path.basename(file_name)
            final_file = os.path.join(youtube_path,filename)

            if (res_youtube == False):
                os.chmod(youtube_path, 0o777)
                logger.logger.info(f'DOWNLOADED ==> {total_downloads} VIDEO YOUTUBE [{file_name}] [{youtube_path}][{filename}]')
                end_time_short = time.strftime('%H:%M', time.localtime())
                await message.edit(f'Downloading finished {total_downloads} video at {end_time_short}\n{youtube_path}')
                self.change_permissions(final_file)
            else:
                logger.logger.info(f'ERROR: ONE OR MORE YOUTUBE VIDEOS NOT DOWNLOADED [{total_downloads}] [{url}] [{youtube_path}]')
                await message.edit(f'ERROR: one or more videos not downloaded') 

    async def downloadAudio(self, url, message):
        os.makedirs(self.constants.get_variable("YOUTUBE_AUDIOS_FOLDER"), exist_ok=True)
        youtube_path = os.path.join(self.constants.get_variable("YOUTUBE_AUDIOS_FOLDER"))
        self.change_permissions(youtube_path)

        logger.logger.info(f'downloadAudio [{url}] [{message}]')
        
        #ydl_opts.update(self.ydl_opts)

        ydl_opts = {
            'format': self.constants.get_variable("YOUTUBE_FORMAT_AUDIO"),  
            'postprocessors': [{
                'key': 'FFmpegExtractAudio', 
                'preferredcodec': 'mp3',     
                'preferredquality': '320',   
            }],
            'outtmpl': os.path.join(youtube_path, '%(title)s.%(ext)s'),
            'merge_output_format':'mp3'
        }

        with YoutubeDL(ydl_opts) as ydl:

            info_dict = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info_dict)[:-5] + ".mp3" if ydl.prepare_filename(info_dict).endswith(".webm") else ydl.prepare_filename(info_dict)
            logger.logger.info(f'DOWNLOADING AUDIO YOUTUBE 1 [{url}] [{file_name}]')
            
            total_downloads = 1
            if '_type' in info_dict and info_dict["_type"] == 'playlist':
                total_downloads = len(info_dict['entries'])
                await message.edit(f'finding {total_downloads} audios...')
        logger.logger.info(f'downloadAudio total_downloads: [{total_downloads}]')

        with YoutubeDL(ydl_opts) as ydl:
            await message.edit(f'downloading {total_downloads} audios...')
            
            res_youtube = ydl.download([url])

            if (res_youtube == False):
                logger.logger.info(f'downloadAudio destination: [{file_name}]')
                os.chmod(self.constants.get_variable("YOUTUBE_AUDIOS_FOLDER"), 0o777)
                end_time_short = time.strftime('%H:%M', time.localtime())
                await message.edit(f'Downloading finished {total_downloads} audio at {end_time_short}\n{youtube_path}')
                self.change_permissions(file_name)
                return file_name
        return None

    def change_permissions(self, path):
        logger.logger.info(f'change_permissions [{path}]')
        try:
            if hasattr(self.constants, 'PUID') and hasattr(self.constants, 'PGID') and self.constants.PUID is not None and self.constants.PGID is not None:
                PUID = int(self.constants.get_variable("PUID")) if (str(self.constants.get_variable("PUID"))).isdigit() else None
                PGID = int(self.constants.get_variable("PGID")) if (str(self.constants.get_variable("PGID"))).isdigit() else None
                if os.path.exists(path): 
                    os.chown(path, PUID, PGID)
                    os.chmod(path, 0o755)  # Cambiar permisos a 755 (rwxr-xr-x)
                    logger.logger.info(f"Changed permissions for {path} using PUID={self.constants.PUID} and PGID={self.constants.PGID}")
        except FileNotFoundError as e:
            logger.logger.error(f"File or directory not found: {path} => {e}")

