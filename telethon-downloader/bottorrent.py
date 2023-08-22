from telethon import TelegramClient, events
from telethon.tl.custom import Button
from telethon.tl.types import MessageMediaPhoto, DocumentAttributeFilename, MessageMediaWebPage
from telethon.utils import get_peer_id, resolve_id

import os
import ast
import time
import shutil
import asyncio
from pathlib import Path

import constants
import logger
import config_manager
from youtube import YouTubeDownloader


class TelegramBot:
    def __init__(self):
        
        self.VERSION = "3.2.1"
        self.SESSION = constants.SESSION
        self.API_ID = constants.API_ID
        self.API_HASH = constants.API_HASH
        self.BOT_TOKEN = constants.BOT_TOKEN
        
        self.TG_AUTHORIZED_USER_ID = constants.TG_AUTHORIZED_USER_ID.replace(" ", "").split(",")
        self.TG_PROGRESS_DOWNLOAD = (constants.TG_PROGRESS_DOWNLOAD == "True" or constants.TG_PROGRESS_DOWNLOAD == True)
        self.TG_MAX_PARALLEL = constants.TG_MAX_PARALLEL
        self.PROGRESS_STATUS_SHOW = int(constants.PROGRESS_STATUS_SHOW)

        self.max_retries = 3
        self.semaphore = asyncio.Semaphore(self.TG_MAX_PARALLEL) 

        self.TG_DOWNLOAD_PATH = constants.TG_DOWNLOAD_PATH
        self.TG_DOWNLOAD_PATH_TORRENTS = constants.TG_DOWNLOAD_PATH_TORRENTS
        self.PATH_TMP = constants.PATH_TMP
        self.PATH_COMPLETED = constants.PATH_COMPLETED
        self.PATH_YOUTUBE = constants.PATH_YOUTUBE

        self.PATH_CONFIG = constants.PATH_CONFIG
        self.CONFIG_MANAGER = config_manager.ConfigurationManager(self.PATH_CONFIG)

        self.DEFAULT_PATH_EXTENSIONS = self.CONFIG_MANAGER.get_section_keys('DEFAULT_PATH')

        self.YOUTUBE_LINKS_SOPORTED = constants.YOUTUBE_LINKS_SOPORTED.replace(" ", "").split(",")

        self.client = TelegramClient(self.SESSION, self.API_ID, self.API_HASH)
        self.client.add_event_handler(self.handle_new_message, events.NewMessage)
        self.client.add_event_handler(self.handle_buttons, events.CallbackQuery)
        
        self.ytdownloader = YouTubeDownloader()


        
        self.environment()
        self.create_directorys()

    async def start(self):
        await self.client.start(bot_token=str(self.BOT_TOKEN))
        await self.client.send_message(6537360, "Telethon Downloader Started: {}".format(self.VERSION))
        logger.logger.info("********** START TELETHON DOWNLOADER **********")
        await self.client.run_until_disconnected()

    def create_directorys(self):
        self.create_directory(self.PATH_TMP)
        self.create_directory(self.PATH_COMPLETED)
        self.create_directory(self.PATH_YOUTUBE)

    def environment(self):
        logger.logger.info(f"API_ID {self.API_ID}")
        logger.logger.info(f"API_HASH {self.API_HASH}")

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
            if self.AUTHORIZED_USER(event.message):
                if event.media:
                    await self.download_media_with_retries(event.media, event.message)
                elif event.message.message:
                    await self.processMessage(event.media, event.message)
        except Exception as e:
            message = await event.reply(f'Exception in hanld enew message: {e}')

    async def handle_buttons(self, event):
        logger.logger.info(f'handle_buttons => event: {event}')
        logger.logger.info(f'handle_buttons => data: {event.data}')
        
        await event.edit('Thank you for clicking video')

        data = event.data
        decoded_data = data.decode('utf-8')
        parsed_data = ast.literal_eval(decoded_data)

        url = parsed_data['url']
        option = parsed_data['option']

        logger.logger.info(f'handle_buttons => data: [{option}] => [{url}]')

        self.create_directory(self.PATH_YOUTUBE)
        async with self.semaphore:
            #msg = await message.reply("Descargando...")
            await self.ytdownloader.download(url)
            #msg = await msg.edit("Descarga completada.")

    async def download_media_with_retries(self, media, message, retry_count=0):
        try:
            await self.download_media(media, message)
        except Exception as e:
            if retry_count < self.max_retries:
                logger.logger.error(f"Descarga fallida, reintentando... Intento {retry_count + 1}")
                await self.download_media_with_retries(media, message, retry_count + 1)
            else:
                logger.logger.error(f"Descarga fallida después de {self.max_retries} intentos")

    async def download_media(self, media, message):
        logger.logger.info(f'download_media => media: {media}')
        logger.logger.info(f'download_media => message: {message}')
        logger.logger.info(f'download_media => fwd_from: {message.fwd_from}')

        #logger.logger.info(f'download_media => from_id: {message.fwd_from.from_id}')
        #logger.logger.info(f'download_media => from_id channel_id: {message.fwd_from.from_id.channel_id}')
        #group_name = await self.get_group_name(int(message.fwd_from.from_id.channel_id))
        #logger.logger.info(f'download_media => group_name: {group_name}')
        
        message = await message.reply(f'Download in queue...')

        async with self.semaphore:
            if isinstance(media, MessageMediaWebPage):
                logger.logger.info(f'download_media => MessageMediaWebPage')
                await self.downloadMessageMediaWebPage(media, message)
        
            if isinstance(media, MessageMediaPhoto):
                await self.downloadMessageMediaPhoto(media, message)

            elif media and hasattr(media, 'document'):
                await self.downloadDocumentAttributeFilename(media, message)

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
                message_text = f'Descargando: {megabytes_current:.2f} MB / {megabytes_total:.2f} MB'
                if current == total or current % (self.PROGRESS_STATUS_SHOW * 1024 * 1024) == 0:
                    await self.client.edit_message(message.chat_id, message.id, message_text)
            finally:
                #logger.logger.error(f'callback Exception: {e}')
                pass
            
        return callback

    async def downloadMessageMediaWebPage(self, media, message):
        logger.logger.info(f'downloadMessageMediaWebPage => media: {media}')
        logger.logger.info(f'downloadMessageMediaWebPage => message: {message.message}')
        if any(yt in message.message for yt in self.YOUTUBE_LINKS_SOPORTED):
            await self.youTubeDownloader(media, message)

    async def downloadMessageMediaPhoto(self, media, message):
        try:
            logger.logger.info(f'downloadMessageMediaPhoto')
            #message = await message.edit(f'Comenzando descarga en: {self.PATH_TMP}')
            #archivo_descarga = await self.client.download_media(media.photo, file=self.PATH_TMP)
            #archivo_descarga = self.moveFile(archivo_descarga)
            #logger.logger.info(f'Foto descargada en: {archivo_descarga}')
            #message = await message.edit(f'Archivo descargado con éxito en: {archivo_descarga}')
            await self.download(media.photo, message, media.photo.size)
        except Exception as e:
            message = await message.edit(f'Exception download: {e}')

    async def downloadDocumentAttributeFilename(self, media, message):
        try:
            logger.logger.info(f'downloadDocumentAttributeFilename')
            for attr in media.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    #message = await message.edit(f'Comenzando descarga en: {self.PATH_TMP}')
                    #archivo_descarga = await self.client.download_media(media.document, file=self.PATH_TMP, progress_callback=self.progress_callback(message))
                    #archivo_descarga = self.moveFile(archivo_descarga)
                    #end_time_short = time.strftime('%H:%M', time.localtime())
                    #logger.logger.info(f'Archivo descargado en: {archivo_descarga}')
                    #message = await message.edit(f'Archivo descargado con éxito en: {archivo_descarga}\n at: {end_time_short}')

                    await self.download(media.document, message, media.document.size)
        except Exception as e:
            message = await message.edit(f'Exception download: {e}')


    async def download(self, media, message, total_size):
        logger.logger.info(f'\n\ndownload media: {media}')
        logger.logger.info(f'\n\ndownload message: {message}')
        try:
            megabytes_total = total_size / 1024 / 1024
            download_start_time = time.time()
            
            
            message = await message.edit(f'Descargando en: {self.PATH_TMP}')
            archivo_descarga = await self.client.download_media(media, file=self.PATH_TMP, progress_callback=self.progress_callback(message))
            archivo_descarga = self.moveFile(archivo_descarga)
            end_time_short = time.strftime('%H:%M', time.localtime())
            logger.logger.info(f'Archivo descargado en: {archivo_descarga}')
            download_end_time = time.time()
            elapsed_time_total = download_end_time - download_start_time
            total_speed = megabytes_total / elapsed_time_total if elapsed_time_total > 0 else 0

            final_message = f'Archivo descargado en: {archivo_descarga}\n'
            final_message += f'Descarga completada en: {elapsed_time_total:.2f} segundos\n'
            final_message += f'Velocidad promedio de descarga: {total_speed:.2f} MB/s\n'
            final_message += f'at: {end_time_short}'
            message = await message.edit(f'{final_message}')

        except Exception as e:
            logger.logger.error(f'download Exception')




    def moveFile(self, file_path):
        try:
            final_path = None

            path_obj = Path(file_path)

            basename = path_obj.name
            filename = path_obj.stem
            extension = path_obj.suffix
            directory = path_obj.parent

            logger.logger.info(f"Full Path: {file_path}")
            logger.logger.info(f"basename: {basename}")
            logger.logger.info(f"Filename: {filename}")
            logger.logger.info(f"Extension: {extension}")
            logger.logger.info(f"Directory: {directory}")
            

            if file_path.endswith('.torrent'): 
                final_path = os.path.join(self.TG_DOWNLOAD_PATH_TORRENTS, basename)
            elif extension[1:] in self.DEFAULT_PATH_EXTENSIONS:
                final_path = os.path.join(self.CONFIG_MANAGER.get_value('DEFAULT_PATH', extension[1:]), basename)
            else:
                final_path = os.path.join(self.PATH_COMPLETED, basename)

            logger.logger.info(f"final_path: {final_path}")

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
            logger.logger.info(f"final_path: {final_path}")

            self.postProcess(final_path)
            return final_path

        except Exception as e:
            logger.logger.error(f'create_directory Exception : {file_path} [{e}]')

    def create_directory(self, path):
        try:
            logger.logger.info(f'create_directory path: {path}')
            os.makedirs(path, exist_ok=True)
            os.chmod(path, 0o777)
        except Exception as e:
            logger.logger.error(f'create_directory Exception : {file_path} [{e}]')

    def postProcess(self, path):
        try:
            logger.logger.info(f'postProcess path: {path}')
        except Exception as e:
            logger.logger.error(f'postProcess Exception : {path} [{e}]')


    async def processMessage(self, media, message):
        logger.logger.info(f'processMessage => media: {media}')
        logger.logger.info(f'processMessage => message: {message.message}')

        if (message.message).startswith('/'):
            await self.commands(message)
        if any(yt in message.message for yt in self.YOUTUBE_LINKS_SOPORTED):
            await self.youTubeDownloader(media, message)

    async def youTubeDownloader(self, media, message):
        logger.logger.info(f'youTubeDownloader => media: {media}')
        logger.logger.info(f'youTubeDownloader => message: {message.message}')

        response = await message.reply('Downloading:', buttons=[
            [
                Button.inline('audio', data={"url":message.message, "option": "audio"}), 
                Button.inline('video', data={"url":message.message, "option": "video"})
            ]
        ])


        #self.create_directory(self.PATH_YOUTUBE)
        #async with self.semaphore:
        #    video_url = message.message
        #    #msg = await message.reply("Descargando...")
        #    await self.ytdownloader.download(video_url)
        #    #msg = await msg.edit("Descarga completada.")

    async def commands(self, message):
        try:
            logger.logger.info(f'commands => message: {message}')

            if message.message == '/version':
                message = await message.reply(f'version: {self.VERSION}')

            if message.message == '/id':
                real_id = get_peer_id(message.peer_id)
                logger.logger.info(f'commands => real_id: {real_id}')
                message = await message.reply(f'id: {str(real_id)}')

        except Exception as e:
            logger.logger.error(f'commands => Exception: {e}')


if __name__ == '__main__':
    
    bot = TelegramBot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start())
