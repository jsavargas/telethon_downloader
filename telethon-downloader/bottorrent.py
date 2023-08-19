from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, DocumentAttributeFilename, MessageMediaWebPage
from telethon.utils import get_peer_id, resolve_id

import os
import shutil
import asyncio
from pathlib import Path

import constants
import logger
import config_manager


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

        self.TG_DOWNLOAD_PATH = constants.TG_DOWNLOAD_PATH
        self.TG_DOWNLOAD_PATH_TORRENTS = constants.TG_DOWNLOAD_PATH_TORRENTS
        self.PATH_TMP = constants.PATH_TMP
        self.PATH_COMPLETED = constants.PATH_COMPLETED
        self.PATH_YOUTUBE = constants.PATH_YOUTUBE

        self.PATH_CONFIG = constants.PATH_CONFIG
        self.CONFIG_MANAGER = config_manager.ConfigurationManager(self.PATH_CONFIG)

        self.DEFAULT_PATH_EXTENSIONS = self.CONFIG_MANAGER.get_section_keys('DEFAULT_PATH')


        self.client = TelegramClient(self.SESSION, self.API_ID, self.API_HASH, proxy = None, request_retries = 10, flood_sleep_threshold = 120)
        self.client.add_event_handler(self.handle_new_message, events.NewMessage)
        self.semaphore = asyncio.Semaphore(self.TG_MAX_PARALLEL)  # Número máximo de descargas simultáneas
        
        self.environment()
        self.create_directorys()

    def create_directorys(self):
        self.create_directory(self.PATH_TMP)
        self.create_directory(self.PATH_COMPLETED)

    def environment(self):
        logger.logger.info(f"API_ID {self.API_ID}")
        logger.logger.info(f"API_HASH {self.API_HASH}")


    async def start(self):
        await self.client.start(bot_token=str(self.BOT_TOKEN))
        await self.client.send_message(6537360, "Telethon Downloader Started: {}".format(self.VERSION))
        logger.logger.info("********** START TELETHON DOWNLOADER **********")
        await self.client.run_until_disconnected()

    def AUTHORIZED_USER(self, message):
        real_id = get_peer_id(message.peer_id)
        logger.logger.info(f'AUTHORIZED_USER  real_id: {real_id}')
        if str(real_id) in self.TG_AUTHORIZED_USER_ID: return True
        else:
            logger.info('USUARIO: %s NO AUTORIZADO', real_id)
            return False

    async def handle_new_message(self, event):
        logger.logger.info(f'handle_new_message => event: {event}')
        if self.AUTHORIZED_USER(event.message):
            if event.media:
                await self.download_media(event.media, event.message)


    async def download_media(self, media, message):
        logger.logger.info(f'download_media => media: {media}')
        logger.logger.info(f'download_media => message: {message}')

        async with self.semaphore:
            if isinstance(media, MessageMediaWebPage):
                logger.logger.info(f'download_media => MessageMediaWebPage')
        
            if isinstance(media, MessageMediaPhoto):
                await self.downloadMessageMediaPhoto(media, message)

            elif media and hasattr(media, 'document'):
                await self.downloadDocumentAttributeFilename(media, message)
                
        
    def progress_callback(self, message):
        async def callback(current, total):
            if not self.TG_PROGRESS_DOWNLOAD: return 

            megabytes_current = current / 1024 / 1024
            megabytes_total = total / 1024 / 1024
            message_text = f'Descargando: {megabytes_current:.2f} MB / {megabytes_total:.2f} MB'
            if current == total or current % (5 * 1024 * 1024) == 0:  # Envía mensaje cada 5 MB
                await self.client.edit_message(message.chat_id, message.id, message_text)
        return callback

    async def downloadMessageMediaWebPage(self, media, message):
        logger.logger.info(f'download_media => MessageMediaWebPage')

    async def downloadMessageMediaPhoto(self, media, message):
        logger.logger.info(f'downloadMessageMediaPhoto')
        message = await message.reply(f'Comenzando descarga en: {self.PATH_TMP}')
        archivo_descarga = await self.client.download_media(media.photo, file=self.PATH_TMP)
        archivo_descarga = self.moveFile(archivo_descarga)
        logger.logger.info(f'Foto descargada en: {archivo_descarga}')
        message = await message.edit(f'Archivo descargado con éxito en: {archivo_descarga}')

    async def downloadDocumentAttributeFilename(self, media, message):
        logger.logger.info(f'downloadDocumentAttributeFilename')
        for attr in media.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                message = await message.reply(f'Comenzando descarga en: {self.PATH_TMP}')
                archivo_descarga = await self.client.download_media(media.document, file=self.PATH_TMP, progress_callback=self.progress_callback(message))
                archivo_descarga = self.moveFile(archivo_descarga)
                logger.logger.info(f'Archivo descargado en: {archivo_descarga}')
                message = await message.edit(f'Archivo descargado con éxito en: {archivo_descarga}')


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
            return final_path

        except Exception as e:
            logger.logger.error(f'create_directory Exception : {file_path} [{e}]')


    def create_directory(self, path):
        try:
            logger.logger.info(f'create_directory path: {path}')
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.logger.error(f'create_directory Exception : {file_path} [{e}]')

if __name__ == '__main__':
    
    bot = TelegramBot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start())
