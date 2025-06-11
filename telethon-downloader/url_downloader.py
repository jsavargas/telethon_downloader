import os
import time
import aiohttp
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from env import Env
from utils import Utils
from config_handler import ConfigHandler
from logger_config import logger

class URLDownloader:
    def __init__(self):
        self.default_download_type = os.getenv("DEFAULT_DOWNLOAD_TYPE", "video")
        self.config_handler = ConfigHandler()
        self.utils = Utils()
        self.env = Env()
        self.pending_callbacks = {}  # To store pending callback queries
        self.youtubeLinks = {}
        self.youtubeDownloadsID = {}

    async def download_from_url(self, client: Client, message: Message, url: str):
        
        try:
            origin_group = message.forward_from.id if message.forward_from else message.forward_from_chat.id if message.forward_from_chat else None

            if 'youtube.com' in url or 'youtu.be' in url:
                await self.send_download_options(client, message, url)
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            file_name = url.split("/")[-1]
                            ext = file_name.split('.')[-1]
                            download_path = self.config_handler.get_download_path(message, origin_group, file_name)

                            start_time, start_hour = self.utils.startTime()

                            file_path = os.path.join(download_path, file_name)
                            with open(file_path, 'wb') as f:
                                f.write(await response.read())


                            self.utils.change_permissions(download_path)
                            self.utils.change_permissions(file_path)


                            end_time, end_hour = self.utils.endTime()
                            elapsed_time = self.utils.elapsedTime(start_time, end_time)
                            file_size, size_str = self.utils.getSize(file_path)
                            download_speed = file_size / elapsed_time / 1024  # KB/s
                            
                            download_info = {
                                'file_name': file_name,
                                'download_folder': download_path,
                                'size_str': size_str,
                                'start_hour': start_hour,
                                'end_hour': end_hour,
                                'elapsed_time': elapsed_time,
                                'download_speed': download_speed,
                                'origin_group': origin_group,
                                'message': message
                            }

                            summary = self.utils.create_download_summary(download_info)

                            #await message.reply_text(f"File {file_name} downloaded to: \n{file_path}")
                            await message.reply_text(summary)

        except Exception as e:
            logger.error(f"Exception download_from_url: {e} ")
            await message.reply_text(f"Exception in download_from_url: {url}")


    async def send_download_options(self, client: Client, message: Message, url: str):
        buttons = [
            [InlineKeyboardButton("Download Video", callback_data=f"ytdown_video_{message.id}")],
            [InlineKeyboardButton("Download Audio", callback_data=f"ytdown_audio_{message.id}")],
            [InlineKeyboardButton("Download Both", callback_data=f"ytdown_both_{message.id}")]
        ]

        self.youtubeLinks[message.id] = url

        reply_markup = InlineKeyboardMarkup(buttons)
        prompt_message = await message.reply_text("Choose download type:", reply_markup=reply_markup)
        
        print(f"prompt_message: prompt_message.id [{prompt_message.id}]")

        self.pending_callbacks[prompt_message.id] = {
            "message": prompt_message,
            "url": url,
            "timestamp": asyncio.get_event_loop().time()
        }

        await asyncio.sleep(5)
        
        if prompt_message.id in self.pending_callbacks:
            print(f"default download [{ prompt_message.id}]")
            # No option selected, proceed with default download type
            await self.download_with_default_type(client, prompt_message, url)
            del self.pending_callbacks[prompt_message.id]

        #Delete the prompt message
        #await prompt_message.delete()

    async def download_with_default_type(self, client: Client, message: Message, url: str):
        download_type = self.default_download_type
        await self.download_youtube_content(client, message, url, download_type)

    def progress_hook(self, info, message):

        try:
            if not info['info_dict']['id'] in self.youtubeDownloadsID:
                self.youtubeDownloadsID[info['info_dict']['id']] = {}
                if 'n_entries' in info['info_dict']:
                    logger.info(f"progress_hook Start Descargando title: [{info['info_dict']['_filename']}] ==> [{info['info_dict']['n_entries']}] ==> [{info['info_dict']['playlist_index']}]")
                else:
                    logger.info(f"progress_hook Start Descargando title: [{info['info_dict']['_filename']}] ==> [!!] ==> [{info['info_dict']['playlist_index']}]")
                
                with open("info_dict_finished.txt", "w") as file:
                    file.write(str(info))

            if info['status'] == 'finished':
                logger.info(f"progress_hook Descargando title: [{info['info_dict']['_filename']}]")
                with open("info_dict_finished.txt", "w") as file:
                    file.write(str(info))

            if info["status"] == "downloading":
                percent = info["_percent_str"]
                #logger.info(f"progress_hook Descargando title: {info['info_dict']['title']} [{info['info_dict']['id']}] => [{percent}]")

        except Exception as e:
            logger.error(f"progress_hook Exception: {e}")


    async def download_youtube_content(self, client: Client, message: Message, url: str, download_type: str):
        
        try:
            start_time, start_hour = self.utils.startTime()

            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(self.env.DOWNLOAD_PATH, 'youtube', '%(title)s.%(ext)s'), #'/download/youtube/videos/%(title)s.%(ext)s',
                #"progress_hooks": [self.progress_hook],
                'progress_hooks': [lambda d: self.progress_hook(d, message)],
            }
            
            if download_type == "audio":
                await message.edit("downloading audio")
                
                #ydl_opts['outtmpl'] = os.path.join(self.env.DOWNLOAD_PATH, 'youtube', 'audios', '%(title)s.%(ext)s')
                #ydl_opts['extract_audio'] = True
                #ydl_opts['format'] = 'bestaudio'
                #ydl_opts['postprocessors'] = [{
                #    'key': 'FFmpegExtractAudio',
                #    'preferredcodec': 'mp3',
                #    'preferredquality': '192',
                #}]


                _ydl_opts = {
                    'extract_audio': True, 
                    'format': 'bestaudio',
                    'outtmpl': os.path.join(self.env.DOWNLOAD_PATH, 'youtube', 'audios', '%(title)s.%(ext)s'),
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
                ydl_opts.update(_ydl_opts)

            
            if download_type == "video":
                await message.edit("downloading video")
                ydl_opts['outtmpl'] = os.path.join(self.env.DOWNLOAD_PATH, 'youtube', 'videos', '%(title)s.%(ext)s')
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mkv'
            
            if download_type == "both":
                await message.edit("Coming soon")

                return
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mkv'
            
            start_time = time.time()

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info_dict = ydl.extract_info(url, download=False)
                file_path = ydl.prepare_filename(info_dict)

                logger.info(f"yt_dlp.YoutubeDL file_path: {file_path}")

                if download_type == "audio":
                    file_path = file_path.replace('.webm', '.mp3') if file_path.endswith(".webm") else file_path

                with open("info_dict.txt", "w") as file:
                    file.write(str(info_dict))

                num_videos = 1
                # Verificar si es una lista de reproducción
                if 'entries' in info_dict:
                    num_videos = len(info_dict['entries'])
                    logger.info(f"Número de videos en la lista de reproducción: {num_videos}")
                

                logger.info(f"ydl.download start")
                download_outtmpl = ydl.download([url])
                logger.info(f"ydl.download finish")

                logger.info(f"\nDetalles de la descarga download_outtmpl: [{download_outtmpl}] => [{file_path}]")

            end_time = time.time()
            duration = end_time - start_time


            if download_outtmpl:
                return

            download_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)

            # Datos para mostrar
            download_speed = 0  # La velocidad promedio requiere cálculo adicional
            logger.info(f"\nDetalles de la descarga:")
            logger.info(f"Cantidad de videos descargados: {num_videos}")
            logger.info(f"Archivo: {file_name}")
            logger.info(f"Ruta de descarga: {download_path}")
            logger.info(f"Hora de inicio: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
            logger.info(f"Hora de finalización: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
            logger.info(f"Duración total: {duration:.2f} segundos")

            self.utils.change_permissions(download_path)
            self.utils.change_permissions(file_path)

            end_time, end_hour = self.utils.endTime()
            elapsed_time = self.utils.elapsedTime(start_time, end_time)
            file_size, size_str = self.utils.getSize(file_path)
            download_speed = file_size / elapsed_time / 1024  # KB/s

            download_info = {
                'file_name': file_name if num_videos == 1 else None,
                'download_folder': download_path,
                'size_str': size_str,
                'start_hour': start_hour,
                'end_hour': end_hour,
                'elapsed_time': elapsed_time,
                'download_speed': download_speed,
                'num_videos': num_videos,
                'message': message
            }

            summary = self.utils.create_download_summary(download_info)

            await message.edit(summary)

            self.utils.change_permissions(self.env.DOWNLOAD_PATH)
            self.utils.change_permissions(os.path.join(self.env.DOWNLOAD_PATH, 'youtube'))
            self.utils.change_permissions(os.path.join(self.env.DOWNLOAD_PATH, 'youtube', 'audios'))
            self.utils.change_permissions(os.path.join(self.env.DOWNLOAD_PATH, 'youtube', 'videos'))

        except Exception as e:
            logger.error(f"download_youtube_content Exception: {message}: {e}")
            await message.edit(f"{download_type.capitalize()} downloaded for URL: {url}\n{e}")

    async def handle_callback_query(self, client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        _, download_type, message_id = data.split('_', 2)
        
        url = self.youtubeLinks[int(message_id)]
        removed_value = self.youtubeLinks.pop(int(message_id))

        print(f"callback_query url: [{url}]")
        print(f"callback_query removed_value: [{removed_value}]")
        print(f"callback_query.message.id: [{callback_query.message.id}]")
        print(f"callback_query.message.id pending_callbacks: [{self.pending_callbacks}]")

        if callback_query.message.id in self.pending_callbacks:
            print(f"default download delete [{callback_query.message.id}]")

            del self.pending_callbacks[callback_query.message.id]

        await self.download_youtube_content(client, callback_query.message, url, download_type)
        #await callback_query.message.edit_text(f"{download_type.capitalize()} downloaded for URL: {url}")



