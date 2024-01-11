#!/usr/bin/env python3

from telethon import TelegramClient, events
from telethon.tl.custom import Button
from telethon.tl.types import MessageMediaPhoto, DocumentAttributeFilename, MessageMediaWebPage
from telethon.utils import get_peer_id, resolve_id

import os
import re
import ast
import time
import shutil
import asyncio
import requests
from pathlib import Path
from urllib.parse import urlparse

import logger
import config_manager
from constants import EnvironmentReader
from youtube import YouTubeDownloader
from command_handler import CommandHandler
from language_templates import LanguageTemplates


class TelegramBot:
    def __init__(self):

        self.constants = EnvironmentReader()
        self.templatesLanguage = LanguageTemplates(language=self.constants.get_variable("LANGUAGE"))

        self.VERSION = "3.1.1.101"
        self.SESSION = self.constants.get_variable("SESSION")
        self.API_ID = self.constants.get_variable("API_ID")
        self.API_HASH = self.constants.get_variable("API_HASH")
        self.BOT_TOKEN = self.constants.get_variable("BOT_TOKEN")
        
        self.PUID = int(self.constants.get_variable("PUID")) if (str(self.constants.get_variable("PUID"))).isdigit() else None
        self.PGID = int(self.constants.get_variable("PGID")) if (str(self.constants.get_variable("PGID"))).isdigit() else None
        
        self.TG_DL_TIMEOUT = int(self.constants.get_variable("TG_DL_TIMEOUT")) if (str(self.constants.get_variable("TG_DL_TIMEOUT"))).isdigit() else 3600

        self.TG_AUTHORIZED_USER_ID = self.constants.get_variable("TG_AUTHORIZED_USER_ID").replace(" ", "").split(",")
        self.TG_PROGRESS_DOWNLOAD = (self.constants.get_variable("TG_PROGRESS_DOWNLOAD") == "True" or self.constants.get_variable("TG_PROGRESS_DOWNLOAD") == True)
        self.TG_MAX_PARALLEL = self.constants.get_variable("TG_MAX_PARALLEL")
        self.PROGRESS_STATUS_SHOW = int(self.constants.get_variable("PROGRESS_STATUS_SHOW"))

        self.max_retries = 3
        self.semaphore = asyncio.Semaphore(self.TG_MAX_PARALLEL) 

        self.TG_DOWNLOAD_PATH = self.constants.get_variable("TG_DOWNLOAD_PATH")
        self.PATH_COMPLETED = self.constants.get_variable("PATH_COMPLETED")
        self.PATH_YOUTUBE = self.constants.get_variable("PATH_YOUTUBE")
        self.PATH_LINKS = self.constants.get_variable("PATH_LINKS")
        self.PATH_TMP = self.constants.get_variable("PATH_TMP")
        self.TG_DOWNLOAD_PATH_TORRENTS = self.constants.get_variable("TG_DOWNLOAD_PATH_TORRENTS")

        self.PATH_CONFIG = self.constants.get_variable("PATH_CONFIG")
        self.CONFIG_MANAGER = config_manager.ConfigurationManager(self.PATH_CONFIG)

        self.DEFAULT_PATH_EXTENSIONS = self.CONFIG_MANAGER.get_section_keys('DEFAULT_PATH')

        self.YOUTUBE_LINKS_SOPORTED = self.constants.get_variable("YOUTUBE_LINKS_SOPORTED").replace(" ", "").split(",")
        self.YOUTUBE_DEFAULT_DOWNLOAD = self.constants.get_variable("YOUTUBE_DEFAULT_DOWNLOAD")
        self.YOUTUBE_TIMEOUT_OPTION = int(self.constants.get_variable("YOUTUBE_TIMEOUT_OPTION")) if (str(self.constants.get_variable("YOUTUBE_TIMEOUT_OPTION"))).isdigit() else 5 
        self.YOUTUBE_SHOW_OPTION = (self.constants.get_variable("YOUTUBE_SHOW_OPTION") == "True" or self.constants.get_variable("YOUTUBE_SHOW_OPTION") == True)
        
        self.youtubeLinks = {}  

        self.client = TelegramClient(self.SESSION, self.API_ID, self.API_HASH, proxy = None, request_retries = 10, flood_sleep_threshold = 120)
        self.client.add_event_handler(self.handle_new_message, events.NewMessage)
        self.client.add_event_handler(self.handle_buttons, events.CallbackQuery)
        
        self.ytdownloader = YouTubeDownloader()
        self.command_handler = CommandHandler(self)


        
        self.printEnvironment()
        self.create_directorys()

    async def start(self):
        await self.client.start(bot_token=str(self.BOT_TOKEN))
        msg_txt = self.templatesLanguage.template("WELCOME").format(msg1=self.VERSION)
        await self.client.send_message(int(self.TG_AUTHORIZED_USER_ID[0]) , msg_txt)
        logger.logger.info("********** START TELETHON DOWNLOADER **********")
        await self.client.run_until_disconnected()

    def printEnvironment(self):
        self.printAttributeHidden("API_ID")
        self.printAttributeHidden("API_HASH")
        self.printAttributeHidden("BOT_TOKEN")
        self.printAttribute("TG_AUTHORIZED_USER_ID")
        self.printAttribute("PUID")
        self.printAttribute("PGID")
        self.printAttribute("TG_DL_TIMEOUT")
        self.printAttribute("YOUTUBE_FORMAT_AUDIO")
        self.printAttribute("YOUTUBE_FORMAT_VIDEO")
        self.printAttribute("YOUTUBE_DEFAULT_DOWNLOAD")
        self.printAttribute("YOUTUBE_TIMEOUT_OPTION")
        self.printAttribute("YOUTUBE_SHOW_OPTION")

        self.printAttribute("LANGUAGE")

        self.printAttribute("VERSION")

    def printAttribute(self, attribute_name):
        if hasattr(self, attribute_name):
            attribute_value = getattr(self, attribute_name)
            logger.logger.info(f"{attribute_name}: {attribute_value}")
        else:
            attribute_value = getattr(self.constants, attribute_name)
            logger.logger.info(f"{attribute_name}: {attribute_value}")

    def printAttributeHidden(self, attribute_name):
        if hasattr(self, attribute_name):
            attribute_value = getattr(self, attribute_name)
            
            half_len = len(attribute_value) // 3
            attribute_value = attribute_value[:half_len] + '*' * (len(attribute_value) - half_len)


            logger.logger.info(f"{attribute_name}: {attribute_value}")
        else:
            attribute_value = getattr(self.constants, attribute_name)
            half_len = len(attribute_value) // 2
            attribute_value = attribute_value[:half_len] + '*' * (len(attribute_value) - half_len)
            logger.logger.info(f"{attribute_name}: {attribute_value}")

    def create_directorys(self):
        self.create_directory(self.TG_DOWNLOAD_PATH)
        self.create_directory(self.PATH_TMP)
        self.create_directory(self.PATH_COMPLETED)
        self.create_directory(self.PATH_YOUTUBE)

    def AUTHORIZED_USER(self, message):
        real_id = get_peer_id(message.peer_id)
        logger.logger.info(f'AUTHORIZED_USER  real_id: {real_id}')
        if str(real_id) in self.TG_AUTHORIZED_USER_ID: return True
        else:
            logger.logger.info('USUARIO: %s NO AUTORIZADO', real_id)
            return False

    async def handle_new_message(self, event):
        try:
            logger.logger.info(f'handle_new_message => event: {event}')
            logger.logger.info(f'handle_new_message => message: {event.message.message}')
            if (event.message.message).startswith('/'):
                await self.commands(event.message)

            elif self.AUTHORIZED_USER(event.message):
                #await self.downloadLinks(message, media, text)
                #if event.media:
                await self.download_media_with_retries(event, event.media, event.message)
                #elif event.message.message:
                #    await self.processMessage(event.media, event.message)
        except Exception as e:
            logger.logger.error(f"handle_new_message: {e}")
            message = await event.reply(f'Exception in hanld enew message: {e}')

    async def handle_buttons(self, event):
        logger.logger.info(f'handle_buttons => event: {event}')
        logger.logger.info(f'handle_buttons => data: {event.data}')
        
        #await event.edit('Thank you for clicking video')

        bytes_data = event.data
        data_string = bytes_data.decode('utf-8')
        data_list = data_string.split(',')

        logger.logger.info(f'handle_buttons => self.youtubeLinks: {self.youtubeLinks}')
        url = self.youtubeLinks[int(data_list[0])]
        removed_value = self.youtubeLinks.pop(int(data_list[0]))

        logger.logger.info(f'handle_buttons => url: {url} => {removed_value}')
        logger.logger.info(f'handle_buttons => data: [{url}] => [{data_list[1]}]')

        self.create_directory(self.PATH_YOUTUBE)
        async with self.semaphore:
            if data_list[1] == 'V':
                await event.edit('Downloading video')
                await self.ytdownloader.downloadVideo(url, event)
            if data_list[1] == 'A':
                await event.edit('Downloading Audio')
                await self.ytdownloader.downloadAudio(url, event)

    async def download_media_with_retries(self, event, media, message, retry_count=0):
        try:
            await self.download_media(event, media, message)
        except Exception as e:
            if retry_count < self.max_retries:
                logger.logger.error(f"Download failed, retrying... Attempt {retry_count + 1}")
                await self.download_media_with_retries(media, message, retry_count + 1)
            else:
                logger.logger.error(f"Download failed after {self.max_retries} attempts")

    async def download_media(self, event, media, message):
        logger.logger.info(f'download_media => media: {media}')
        logger.logger.info(f'download_media => message: {message}')
        logger.logger.info(f'download_media => fwd_from: {message.fwd_from}')
        
        text = message.message
        message = await message.reply(f'Download in queue...')

        async with self.semaphore:
            message = await message.edit(f'Download in progress')

            if isinstance(media, MessageMediaWebPage):
                logger.logger.info(f'download_media => MessageMediaWebPage')
                await self.downloadMessageMediaWebPage(event, message, media, text)
        
            elif isinstance(media, MessageMediaPhoto):
                await self.downloadMessageMediaPhoto(event, message, media)

            elif media and hasattr(media, 'document'):
                await self.downloadDocumentAttributeFilename(event, message, media)

            else:
                logger.logger.info(f'download_media NO MEDIA')
                await self.downloadLinks(message, media, text)

    async def get_group_name(self, chat_id):
        try:
            chat = await self.client.get_entity(chat_id)
            if hasattr(chat, 'title'):
                return chat.title
            return None
        except Exception as e:
            return None
               
    def progress_callback(self, message):
        async def callback(current, total):
            if not self.TG_PROGRESS_DOWNLOAD: return 
            try:
                megabytes_current = current / 1024 / 1024
                megabytes_total = total / 1024 / 1024
                message_text = f'Downloading in: {self.PATH_TMP}\n'
                message_text += f'progress: {megabytes_current:.2f} MB / {megabytes_total:.2f} MB'
                message_text = self.templatesLanguage.template("PROGRESS_CALLBACK_PATH").format(path=self.PATH_TMP)   # Add a line separator at the end
                message_text += self.templatesLanguage.template("PROGRESS_CALLBACK_PROGRESS").format(current=megabytes_current, total=megabytes_total)
                if current == total or current % (self.PROGRESS_STATUS_SHOW * 1024 * 1024) == 0:
                    await self.client.edit_message(message.chat_id, message.id, message_text)
            finally:
                #logger.logger.error(f'callback Exception: {e}')
                return
            
        return callback

    async def downloadMessageMediaWebPage(self, event, message, media, text):
        logger.logger.info(f'downloadMessageMediaWebPage => message: {message}')
        logger.logger.info(f'downloadMessageMediaWebPage => media: {media}')
        logger.logger.info(f'downloadMessageMediaWebPage => message.message: {text}')

        await self.downloadLinks(message, media, text)
    
    async def downloadMessageMediaPhoto(self, event, message, media):
        try:
            logger.logger.info(f'downloadMessageMediaPhoto')
            
            last_size = 0

            desired_size_type = 'y'  
            for size in media.photo.sizes:
                if hasattr(size, 'size'):
                    logger.logger.info(f"Desired size:::: {size}")
                    last_size = size.size if size.size > last_size else last_size

                if hasattr(size, 'sizes'):
                    logger.logger.info(f"Desired size IF: {size}")
                    last_size = size.sizes[-1]
                    break
                                
            logger.logger.info(f'downloadMessageMediaPhoto last_size: {last_size}')
            await self.download(event, message, media.photo, last_size)
        except Exception as e:
            message = await message.edit(f'Exception downloadMessageMediaPhoto: {e}')

    async def downloadDocumentAttributeFilename(self, event, message, media):
        try:
            logger.logger.info(f'downloadDocumentAttributeFilename')
            for attr in media.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):

                    await self.download(event, message, media.document, media.document.size)
        except Exception as e:
            message = await message.edit(f'Exception download: {e}')


    async def download(self, event, message, media, total_size):
        logger.logger.info(f'download media: {media}')
        logger.logger.info(f'download message: {message}')
        try:
            megabytes_total = total_size / 1024 / 1024
            download_start_time = time.time()
            self.create_directory(self.PATH_TMP)

            logger.logger.info(f'download download_start_time temp 1: {download_start_time} download_end_time: {time.time()} elapsed_time_total: {time.time() - download_start_time} total_speed:  ')

            message_text = self.templatesLanguage.template("MESSAGE_DOWNLOAD").format(path=self.PATH_TMP)
            message = await message.edit(message_text)

            logger.logger.info(f'download download_start_time temp 2: {download_start_time} download_end_time: {time.time()} elapsed_time_total: {time.time() - download_start_time} total_speed:  ')

            loop = asyncio.get_event_loop()
            task = loop.create_task(self.client.download_media(event.message, file=self.PATH_TMP, progress_callback=self.progress_callback(message)))

            downloaded_file = await asyncio.wait_for(
                task,
                timeout=self.TG_DL_TIMEOUT
            )
            
            logger.logger.info(f'download download_start_time temp 3: {download_start_time} download_end_time: {time.time()} elapsed_time_total: {time.time() - download_start_time} total_speed:  ')
            logger.logger.info(f'download download_start_time temp 3: {downloaded_file} total_speed:  ')

            downloaded_file = self.moveFile(downloaded_file)
            end_time_short = time.strftime('%H:%M', time.localtime())
            logger.logger.info(f'File downloaded in: {downloaded_file}')
            download_end_time = time.time()
            elapsed_time_total = download_end_time - download_start_time
            total_speed = megabytes_total / elapsed_time_total if elapsed_time_total > 0 else 0

            logger.logger.info(f'download download_start_time temp 4: {download_start_time} download_end_time: {time.time()} elapsed_time_total: {time.time() - download_start_time} total_speed:  ')


            message_text = f'File downloaded in: {downloaded_file}\n'
            message_text += f'Descarga completada en: {elapsed_time_total:.2f} segundos\n'
            message_text += f'Velocidad promedio de descarga: {total_speed:.2f} MB/s\n'
            message_text += f'at: {end_time_short}'

            message_text = self.templatesLanguage.template("MESSAGE_DOWNLOAD_FILE").format(downloaded_file=downloaded_file)   # Add a line separator at the end
            message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_COMPLETED").format(elapsed_time=self.format_time(elapsed_time_total))   # Add a line separator at the end
            message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_SPEED").format(speed=total_speed)   # Add a line separator at the end
            message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_AT").format(end_time=end_time_short)

            logger.logger.info(f'download download_start_time temp 5: {download_start_time} download_end_time: {time.time()} elapsed_time_total: {time.time() - download_start_time} total_speed: {elapsed_time_total} ')

            message = await message.edit(f'{message_text}')

        except asyncio.TimeoutError:
            logger.logger.error("Download timeout exceeded.")
            message_text = self.templatesLanguage.template("MESSAGE_TIMEOUT_EXCEEDED")
            message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_AT").format(end_time=end_time_short)
            message = await message.edit(message_text)
        except Exception as e:
            logger.logger.error(f'download Exception: {e}')
            message = await message.edit(f'Exception download: {e}')

    def moveFile(self, file_path):
        try:
            final_path = None

            path_obj = Path(file_path)

            basename = path_obj.name
            filename = path_obj.stem
            extension = path_obj.suffix
            directory = path_obj.parent

            logger.logger.info(f"moveFile file_path: {file_path}")
            logger.logger.info(f"moveFile basename: {basename}")
            logger.logger.info(f"moveFile Filename: {filename}")
            logger.logger.info(f"moveFile Extension: {extension}")
            logger.logger.info(f"moveFile Directory: {directory}")
            

            if file_path.endswith('.torrent'): 
                final_path = os.path.join(self.TG_DOWNLOAD_PATH_TORRENTS, basename)
            elif extension[1:] in self.DEFAULT_PATH_EXTENSIONS:
                final_path = os.path.join(self.CONFIG_MANAGER.get_value('DEFAULT_PATH', extension[1:]), basename)
            else:
                final_path = os.path.join(self.PATH_COMPLETED, basename)

            logger.logger.info(f"moveFile final_path: {final_path}")

            directorio_base = Path(final_path).parent            
            if os.path.exists(final_path):
                destination_filename = basename    
                counter = 1
                while os.path.exists(os.path.join(directorio_base, destination_filename)):
                    destination_filename = f"{filename} ({counter}){extension}"
                    counter += 1        
                final_path = os.path.join(directorio_base, destination_filename)        

            self.create_directory(directorio_base)
            final_path = shutil.move(file_path, final_path)
            self.change_permissions(final_path)
            logger.logger.info(f"moveFile final_path: {final_path}")

            self.postProcess(final_path)
            return final_path

        except Exception as e:
            logger.logger.error(f'moveFile Exception : {file_path} [{e}]')

    def create_directory(self, path):
        try:
            logger.logger.info(f'create_directory path: {path}')
            os.makedirs(path, exist_ok=True)
            if hasattr(self, 'PUID') and hasattr(self, 'PGID') and self.PUID is not None and self.PGID is not None:
                if os.path.exists(path): os.chown(path, self.PUID, self.PGID)
            if os.path.exists(path): os.chmod(path, 0o777)
        except Exception as e:
            logger.logger.error(f'create_directory Exception : {path} [{e}]')

    def change_permissions(self, path):
        try:
            if hasattr(self, 'PUID') and hasattr(self, 'PGID') and self.PUID is not None and self.PGID is not None:
                if os.path.exists(path): os.chown(path, self.PUID, self.PGID)
            if os.path.exists(path): os.chmod(path, 0o755)  # Cambiar permisos a 755 (rwxr-xr-x)
            logger.logger.info(f"Changed permissions for {path} using PUID={self.PUID} and PGID={self.PGID}")
        except FileNotFoundError:
            logger.logger.error(f"File or directory not found: {path}")

    def postProcess(self, path):
        try:
            logger.logger.info(f'postProcess path: {path}')
        except Exception as e:
            logger.logger.error(f'postProcess Exception : {path} [{e}]')
        
    async def downloadLinks(self, message, media, text):
        logger.logger.info(f'downloadLinks => media: {media}')
        logger.logger.info(f'downloadLinks => message: {message.message}')
        logger.logger.info(f'downloadLinks => text: {text}')

        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        urls = re.findall(url_pattern, text)

        tasks = []

        for url in urls:
            if any(yt in url for yt in self.YOUTUBE_LINKS_SOPORTED):
                task = self.youTubeDownloader(message, url)
                tasks.append(task)
            elif all([urlparse(url).scheme, urlparse(url).netloc]):
                task = self.download_url_file(message, url)
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks)
        else:
            logger.logger.info(f'downloadLinks => NO ULRS: {urls}')
            await message.edit(self.templatesLanguage.template("MESSAGE_NO_LINKS_DOWNLOAD"))

    async def youTubeDownloader(self, message, text):
        try:
            logger.logger.info(f'youTubeDownloader => media: {message}')
            logger.logger.info(f'youTubeDownloader => text: "{text}"')
            logger.logger.info(f'youTubeDownloader => message.id: "{message.id}"')
            
            self.youtubeLinks[message.id] = text

            if self.YOUTUBE_SHOW_OPTION:
                button1 = Button.inline("Audio", data=f"{message.id},A")
                button2 = Button.inline("Video", data=f"{message.id},V")

                response = await message.edit('Downloading:', buttons=[button1, button2])

                await asyncio.sleep(self.YOUTUBE_TIMEOUT_OPTION)

            logger.logger.info(f'youTubeDownloader => self.youtubeLinks: {self.youtubeLinks} => {message.id}')

            if message.id in self.youtubeLinks:            
                removed_value = self.youtubeLinks.pop(int(message.id))
                if self.YOUTUBE_DEFAULT_DOWNLOAD.upper() == 'VIDEO':
                    await message.edit('Downloading video')
                    await self.ytdownloader.downloadVideo(text, message)
                if self.YOUTUBE_DEFAULT_DOWNLOAD.upper() == 'AUDIO':
                    await message.edit('Downloading Audio')
                    await self.ytdownloader.downloadAudio(text, message)
        except Exception as e:
            logger.logger.error(f'youTubeDownloader => Exception: {e}')
            await message.reply(f'Error: {e}')
            pass

    async def download_url_file(self, message, url):
        try:
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            
            download_start_time = time.time()

            response = requests.head(url, allow_redirects=True)
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                logger.logger.info(f'download_url_file => NO DOWNLOADED LINK: {url}')
                message = await message.edit(self.templatesLanguage.template("MESSAGE_NO_LINKS_DOWNLOAD"))
                return 

            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file_path = os.path.join(self.PATH_LINKS, file_name)
                message = await message.edit(self.templatesLanguage.template("MESSAGE_DOWNLOAD").format(path=self.PATH_LINKS))
                self.create_directory(self.PATH_LINKS)
                
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                
                    file_path = self.moveFile(file_path)

                    self.change_permissions(file_path)
                    file_size = len(response.content) / 1024 / 1024 
                    download_end_time = time.time()
                    elapsed_time_total = download_end_time - download_start_time
                    total_speed = file_size / elapsed_time_total if elapsed_time_total > 0 else 0
                    end_time_short = time.strftime('%H:%M', time.localtime())
                    f_elapsed_time_total = self.format_time(elapsed_time_total)

                    message_text = self.templatesLanguage.template("MESSAGE_DOWNLOAD_FILE").format(downloaded_file=file_path)   # Add a line separator at the end
                    message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_FILE_SIZE").format(file_size=file_size)   # Add a line separator at the end
                    message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_COMPLETED").format(elapsed_time=f_elapsed_time_total)   # Add a line separator at the end
                    message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_SPEED").format(speed=total_speed)   # Add a line separator at the end
                    message_text += self.templatesLanguage.template("MESSAGE_DOWNLOAD_AT").format(end_time=end_time_short)

                    message = await message.edit(f'{message_text}')
                    
                    logger.logger.info(f"download_url_file {url}. Status code: {response.status_code} => {file_path}")
                return file_path
            else:
                logger.logger.info(f"download_url_file {url}. Status code: {response.status_code}")
                message = await message.edit(self.templatesLanguage.template("MESSAGE_NO_LINKS_DOWNLOAD"))
                return None
        except Exception as e:
            logger.logger.error(f"download_url_file {url}. {e}")
            message = await message.edit(self.templatesLanguage.template("MESSAGE_NO_LINKS_DOWNLOAD"))

    async def commands(self, message):
        try:
            logger.logger.info(f'commands => message: {message}')
            logger.logger.info(f'commands => message: {message.message}')
            if self.AUTHORIZED_USER(message):
                if message.message == '/help':
                    await self.command_handler.show_help(message)
                if message.message == '/version':
                    await self.command_handler.show_version(message)
            if message.message == '/id':
                await self.command_handler.show_id(message)

        except Exception as e:
            logger.logger.error(f'commands => Exception: {e}')

    def format_time(self, seconds):
        try:
            minutes, seconds = divmod(int(seconds), 60)
            hours, minutes = divmod(minutes, 60)


            #message_text = self.templatesLanguage.template("MESSAGE_DOWNLOAD_FILE").format(downloaded_file=downloaded_file) 

            HOUR=self.templatesLanguage.templateOneLine("HOUR")
            MINUTE=self.templatesLanguage.templateOneLine("MINUTE")
            SECOND=self.templatesLanguage.templateOneLine("SECOND")

            HOURS=self.templatesLanguage.templateOneLine("HOURS")
            MINUTES=self.templatesLanguage.templateOneLine("MINUTES")
            SECONDS=self.templatesLanguage.templateOneLine("SECONDS")

            time_parts = [
                f"{hours} {HOUR}{'s' * (hours != 1)}" if hours else "",
                f"{minutes} {MINUTE}{'s' * (minutes != 1)}" if minutes else "",
                f"{seconds} {SECONDS}" if seconds and (seconds != 1) else ( f"{seconds} {SECOND}" if seconds and (seconds == 1)  else "")
            ]

            formatted_time = " ".join(filter(None, time_parts))
            return formatted_time
        except Exception as e:
            logger.logger.error(f"format_time {seconds}. {e}")
            return seconds

if __name__ == '__main__':
    
    bot = TelegramBot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start())
