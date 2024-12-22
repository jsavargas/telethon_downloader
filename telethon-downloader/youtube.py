from yt_dlp import YoutubeDL

import os
import time
import asyncio

import logger
from constants import EnvironmentReader
from utils import Utils


class YouTubeDownloader:
    def __init__(self):
        self.constants = EnvironmentReader()
        self.utils = Utils()
        self.ydl_opts_VIDEO = {
            "format": self.constants.get_variable("YOUTUBE_FORMAT_VIDEO"),
            "outtmpl": f'{self.constants.get_variable("PATH_YOUTUBE")}/%(title)s.%(ext)s',
            "cachedir": "False",
            "retries": 10,
            "merge_output_format": self.constants.get_variable(
                "YOUTUBE_DEFAULT_EXTENSION"
            ).lower(),
            "progress_hooks": [self.progress_hook],
        }
        self.ydl_opts_AUDIO = {
                'extract_audio': True, 
                'format': self.constants.get_variable('YOUTUBE_FORMAT_AUDIO'),
                "outtmpl": f'{self.constants.get_variable("YOUTUBE_AUDIO_FOLDER")}/%(title)s.%(ext)s',
                'cachedir': 'False',
                'ignoreerrors': True,
                'retries': 10,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }
                ],
            }

    def progress_hook(self, data):
        if data["status"] == "downloading":
            percent = data["_percent_str"]
            logger.logger.info(f"Descargando: {percent}")

    async def downloadVideo(self, url, message):
        logger.logger.info(f"YouTubeDownloader downloadVideo [{url}] [{message}]")

        YOUTUBE_VIDEO_FOLDER = os.path.join(
            self.constants.get_variable("YOUTUBE_VIDEO_FOLDER")
        )

        with YoutubeDL(self.ydl_opts_VIDEO) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info_dict)
            total_downloads = 1
            youtube_path = YOUTUBE_VIDEO_FOLDER
            self.utils.change_owner_permissions(youtube_path)

            if "_type" in info_dict and info_dict["_type"] == "playlist":
                total_downloads = len(info_dict["entries"])
                youtube_path = os.path.join(
                    YOUTUBE_VIDEO_FOLDER,
                    info_dict["uploader"],
                    info_dict["title"],
                )
            else:
                youtube_path = os.path.join(YOUTUBE_VIDEO_FOLDER, info_dict["uploader"])

            ydl_opts = {
                "format": self.constants.get_variable("YOUTUBE_FORMAT_VIDEO"),
                "outtmpl": f"{youtube_path}/%(title)s.%(ext)s",
                "cachedir": "False",
                "ignoreerrors": True,
                "retries": 10,
                "merge_output_format": self.constants.get_variable(
                    "YOUTUBE_DEFAULT_EXTENSION"
                ).lower(),
            }
            ydl_opts.update(ydl_opts)

        with YoutubeDL(ydl_opts) as ydl:
            logger.logger.info(f"DOWNLOADING VIDEO YOUTUBE [{url}] [{file_name}]")
            await message.edit(f"downloading {total_downloads} videos...")
            res_youtube = ydl.download([url])

            filename = os.path.basename(file_name)
            final_file = os.path.join(youtube_path, filename)

            if res_youtube == False:
                os.chmod(youtube_path, 0o777)
                logger.logger.info(
                    f"DOWNLOADED ==> {total_downloads} VIDEO YOUTUBE [{file_name}] [{youtube_path}][{filename}]"
                )
                end_time_short = time.strftime("%H:%M", time.localtime())
                await message.edit(
                    f"Downloading finished {total_downloads} video at {end_time_short}\n{final_file}"
                )
                self.utils.change_owner_permissions(final_file)
            else:
                logger.logger.info(
                    f"ERROR: ONE OR MORE YOUTUBE VIDEOS NOT DOWNLOADED [{total_downloads}] [{url}] [{youtube_path}]"
                )
                await message.edit(f"ERROR: one or more videos not downloaded")

    async def downloadAudio(self, url, message):
        logger.logger.info(f"YouTubeDownloader downloadAudio [{url}] [{message}]")

        YOUTUBE_AUDIO_FOLDER = os.path.join(
            self.constants.get_variable("YOUTUBE_AUDIO_FOLDER")
        )
        self.utils.create_folders(YOUTUBE_AUDIO_FOLDER)


        with YoutubeDL(self.ydl_opts_AUDIO) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info_dict)
            total_downloads = 1
            youtube_path = YOUTUBE_AUDIO_FOLDER
            self.utils.change_owner_permissions(youtube_path)

            if "_type" in info_dict and info_dict["_type"] == "playlist":
                total_downloads = len(info_dict["entries"])
                youtube_path = os.path.join(
                    YOUTUBE_AUDIO_FOLDER,
                    info_dict["uploader"],
                    info_dict["title"],
                )
            else:
                youtube_path = os.path.join(YOUTUBE_AUDIO_FOLDER, info_dict["uploader"])

            ydl_opts = {
                'extract_audio': True, 
                'format': self.constants.get_variable('YOUTUBE_FORMAT_AUDIO'),
                'outtmpl': f'{youtube_path}/%(title)s.%(ext)s',
                'cachedir': 'False',
                'ignoreerrors': True,
                'retries': 10,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }
                ],
            }
            ydl_opts.update(ydl_opts)


        logger.logger.info(f"downloadAudio [{url}] [{message}]")



        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info_dict)

            logger.logger.info(f"DOWNLOADING AUDIO YOUTUBE [{url}] [{file_name}]")
            
            file_name = (
                ydl.prepare_filename(info_dict)[:-4] + ".mp3"
                if ydl.prepare_filename(info_dict).endswith(".m4a")
                else ydl.prepare_filename(info_dict)
            )
            await message.edit(f"downloading {total_downloads} audios...")

            res_youtube = ydl.download([url])

            if res_youtube == False:
                logger.logger.info(f"downloadAudio destination: [{file_name}]")
                os.chmod(self.constants.get_variable("YOUTUBE_AUDIO_FOLDER"), 0o777)
                end_time_short = time.strftime("%H:%M", time.localtime())
                await message.edit(
                    f"Downloading finished {total_downloads} audio at {end_time_short}\n{file_name}"
                )
                self.utils.change_owner_permissions(file_name)
                return file_name
        return None
