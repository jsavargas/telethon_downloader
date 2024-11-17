#!/usr/bin/env python3

from telethon import TelegramClient, events, __version__ as telethon_version
from telethon.tl.custom import Button
from telethon.tl.types import (
    MessageMediaPhoto,
    DocumentAttributeVideo,
    MessageMediaDocument,
    DocumentAttributeFilename,
    MessageMediaWebPage,
    PeerUser,
    PeerChannel,
)
from telethon.utils import get_peer_id, resolve_id
import yt_dlp

import os
import re
import ast
import time
import shutil
import asyncio
import requests
from pathlib import Path
from urllib.parse import urlparse
from datetime import timedelta

import logger
import config_manager
from constants import EnvironmentReader
from youtube import YouTubeDownloader
from command_handler import CommandHandler
from language_templates import LanguageTemplates
from file_extractor import FileExtractor
from download_manager import DownloadPathManager
from pending_messages_handler import PendingMessagesHandler
from db_downloads import DownloadFilesDB
from utils import Utils


class TelegramBot:
    def __init__(self):
        self.BOT_VERSION = "4.0.7"
        self.TELETHON_VERSION = telethon_version
        self.YTDLP_VERSION = yt_dlp.version.__version__

        self.constants = EnvironmentReader()
        self.utils = Utils()
        self.templatesLanguage = LanguageTemplates(
            language=self.constants.get_variable("LANGUAGE")
        )
        self.pendingMessagesHandler = PendingMessagesHandler()
        self.downloadFilesDB = DownloadFilesDB()

        self.SESSION = self.constants.get_variable("SESSION")
        self.API_ID = self.constants.get_variable("API_ID")
        self.API_HASH = self.constants.get_variable("API_HASH")
        self.BOT_TOKEN = self.constants.get_variable("BOT_TOKEN")

        self.PUID = (
            int(self.constants.get_variable("PUID"))
            if (str(self.constants.get_variable("PUID"))).isdigit()
            else None
        )
        self.PGID = (
            int(self.constants.get_variable("PGID"))
            if (str(self.constants.get_variable("PGID"))).isdigit()
            else None
        )

        self.TG_DL_TIMEOUT = (
            int(self.constants.get_variable("TG_DL_TIMEOUT"))
            if (str(self.constants.get_variable("TG_DL_TIMEOUT"))).isdigit()
            else 3600
        )

        self.TG_AUTHORIZED_USER_ID = (
            self.constants.get_variable("TG_AUTHORIZED_USER_ID")
            .replace(" ", "")
            .split(",")
        )
        self.TG_PROGRESS_DOWNLOAD = (
            self.constants.get_variable("TG_PROGRESS_DOWNLOAD") == "True"
            or self.constants.get_variable("TG_PROGRESS_DOWNLOAD") == True
        )
        self.ENABLED_UNZIP = (
            self.constants.get_variable("ENABLED_UNZIP") == "True"
            or self.constants.get_variable("ENABLED_UNZIP") == True
        )
        self.ENABLED_UNRAR = (
            self.constants.get_variable("ENABLED_UNRAR") == "True"
            or self.constants.get_variable("ENABLED_UNRAR") == True
        )
        self.ENABLED_7Z = (
            self.constants.get_variable("ENABLED_7Z") == "True"
            or self.constants.get_variable("ENABLED_7Z") == True
        )
        self.TG_MAX_PARALLEL = self.constants.get_variable("TG_MAX_PARALLEL")
        self.PROGRESS_STATUS_SHOW = int(
            self.constants.get_variable("PROGRESS_STATUS_SHOW")
        )

        self.max_retries = 3
        self.semaphore = asyncio.Semaphore(self.TG_MAX_PARALLEL)

        self.TG_DOWNLOAD_PATH = self.constants.get_variable("TG_DOWNLOAD_PATH")
        self.PATH_COMPLETED = self.constants.get_variable("PATH_COMPLETED")
        self.PATH_YOUTUBE = self.constants.get_variable("PATH_YOUTUBE")
        self.PATH_LINKS = self.constants.get_variable("PATH_LINKS")
        self.PATH_TMP = self.constants.get_variable("PATH_TMP")
        self.TG_DOWNLOAD_PATH_TORRENTS = self.constants.get_variable(
            "TG_DOWNLOAD_PATH_TORRENTS"
        )

        self.PATH_CONFIG = self.constants.get_variable("PATH_CONFIG")

        self.DEFAULT_PATH_EXTENSIONS = self.getConfigurationManager()
        self.GROUP_PATH = self.getConfigurationManager("GROUP_PATH")
        self.SECTIONS = self.getConfigurationManagerAll()

        self.YOUTUBE_LINKS_SUPPORTED = (
            self.constants.get_variable("YOUTUBE_LINKS_SUPPORTED")
            .replace(" ", "")
            .split(",")
        )
        self.YOUTUBE_DEFAULT_DOWNLOAD = self.constants.get_variable(
            "YOUTUBE_DEFAULT_DOWNLOAD"
        )
        self.YOUTUBE_SHOW_OPTION_TIMEOUT = (
            int(self.constants.get_variable("YOUTUBE_SHOW_OPTION_TIMEOUT"))
            if (
                str(self.constants.get_variable("YOUTUBE_SHOW_OPTION_TIMEOUT"))
            ).isdigit()
            else 5
        )
        self.YOUTUBE_SHOW_OPTION = (
            self.constants.get_variable("YOUTUBE_SHOW_OPTION") == "True"
            or self.constants.get_variable("YOUTUBE_SHOW_OPTION") == True
        )

        self.ignored_extensions = os.environ.get("IGNORED_EXTENSIONS", "torrent").split(
            ","
        )

        self.youtubeLinks = {}

        self.client = TelegramClient(
            self.SESSION,
            self.API_ID,
            self.API_HASH,
            proxy=None,
            request_retries=10,
            flood_sleep_threshold=120,
        )
        self.client.add_event_handler(self.handle_new_message, events.NewMessage)
        self.client.add_event_handler(self.handle_buttons, events.CallbackQuery)

        self.ytdownloader = YouTubeDownloader()
        self.command_handler = CommandHandler(self)

        self.printEnvironment()
        self.create_directorys()

    async def start(self):



        await self.client.start(bot_token=str(self.BOT_TOKEN))
        msg_txt = self.templatesLanguage.template("WELCOME")
        msg_txt += self.templatesLanguage.template("BOT_VERSION").format(
            msg1=self.BOT_VERSION
        )
        msg_txt += self.templatesLanguage.template("TELETHON_VERSION").format(
            msg1=self.TELETHON_VERSION
        )
        msg_txt += self.templatesLanguage.template("YTDLP_VERSION").format(
            msg1=self.YTDLP_VERSION
        )
        await self.client.send_message(int(self.TG_AUTHORIZED_USER_ID[0]), msg_txt)
        logger.logger.info("********** START TELETHON DOWNLOADER **********")

        await self.download_pending_messages()

        await self.client.run_until_disconnected()

    async def handle_new_message(self, event):
        try:
            logger.logger.info(f"handle_new_message => event: {event}")

            AUTHORIZED_USER = self.AUTHORIZED_USER(event.message)

            if AUTHORIZED_USER and (event.message.message).startswith("/rename"):
                logger.logger.info(f"handle_new_message => RENAME: {event}")
                await self.renameFilesReply(event)

            elif (event.message.message).startswith("/"):
                await self.commands(event.message)

            elif self.AUTHORIZED_USER(event.message):
                await self.download_media_with_retries(event.message)
        except Exception as e:
            logger.logger.error(f"handle_new_message Exception: {e}")
            await event.reply(f"Exception in hanld enew message: {e}")

    async def handle_buttons(self, event):
        logger.logger.info(f"handle_buttons => event: {event}")
        logger.logger.info(f"handle_buttons => data: {event.data}")

        # await event.edit('Thank you for clicking video')

        bytes_data = event.data
        data_string = bytes_data.decode("utf-8")
        data_list = data_string.split(",")

        logger.logger.info(f"handle_buttons => self.youtubeLinks: {self.youtubeLinks}")
        url = self.youtubeLinks[int(data_list[0])]
        removed_value = self.youtubeLinks.pop(int(data_list[0]))

        logger.logger.info(f"handle_buttons => url: {url} => {removed_value}")
        logger.logger.info(f"handle_buttons => data: [{url}] => [{data_list[1]}]")

        self.utils.create_folders(self.PATH_YOUTUBE)
        async with self.semaphore:
            if data_list[1] == "V":
                await event.edit("Downloading video")
                await self.ytdownloader.downloadVideo(url, event)
            if data_list[1] == "A":
                await event.edit("Downloading Audio")
                await self.ytdownloader.downloadAudio(url, event)

    def printEnvironment(self):
        self.printAttributeHidden("API_ID")
        self.printAttributeHidden("API_HASH")
        self.printAttributeHidden("BOT_TOKEN")
        self.printAttributeHidden("TG_AUTHORIZED_USER_ID")
        self.printAttribute("PUID")
        self.printAttribute("PGID")
        self.printAttribute("TG_MAX_PARALLEL")
        self.printAttribute("TG_DL_TIMEOUT")
        self.printAttribute("TG_PROGRESS_DOWNLOAD")
        self.printAttribute("PROGRESS_STATUS_SHOW")
        self.printAttribute("YOUTUBE_FORMAT_AUDIO")
        self.printAttribute("YOUTUBE_FORMAT_VIDEO")
        self.printAttribute("YOUTUBE_LINKS_SUPPORTED")
        self.printAttribute("YOUTUBE_DEFAULT_DOWNLOAD")
        self.printAttribute("YOUTUBE_DEFAULT_EXTENSION")
        self.printAttribute("YOUTUBE_SHOW_OPTION")
        self.printAttribute("YOUTUBE_SHOW_OPTION_TIMEOUT")
        self.printAttribute("ENABLED_UNZIP")
        self.printAttribute("ENABLED_UNRAR")
        self.printAttribute("ENABLED_7Z")

        self.printAttribute("LANGUAGE")

        self.printAttribute("BOT_VERSION")
        self.printAttribute("TELETHON_VERSION")
        self.printAttribute("YTDLP_VERSION")

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
        else:
            attribute_value = getattr(self.constants, attribute_name)

        if isinstance(attribute_value, list):
            _attribute_value = []
            for value in attribute_value:
                half_len = len(value) // 2
                _attribute_value.append(
                    value[:half_len] + "*" * (len(value) - half_len)
                )
            logger.logger.info(f"{attribute_name}: {_attribute_value}")
        elif isinstance(attribute_value, str):
            half_len = len(attribute_value) // 3
            attribute_value = attribute_value[:half_len] + "*" * (
                len(attribute_value) - half_len
            )
            logger.logger.info(f"{attribute_name}: {attribute_value}")

    def getConfigurationManager(self, section_keys="DEFAULT_PATH"):
        self.CONFIG_MANAGER = config_manager.ConfigurationManager(self.PATH_CONFIG)
        return self.CONFIG_MANAGER.get_section_keys(section_keys)

    def getConfigurationManagerAll(self):
        self.CONFIG_MANAGER = config_manager.ConfigurationManager(self.PATH_CONFIG)
        return self.CONFIG_MANAGER.get_all_sections()

    def create_directorys(self):
        self.utils.create_folders(self.TG_DOWNLOAD_PATH)
        self.utils.create_folders(self.PATH_TMP)
        self.utils.create_folders(self.PATH_COMPLETED)
        self.utils.create_folders(self.PATH_YOUTUBE)

    def AUTHORIZED_USER(self, message):
        real_id = get_peer_id(message.peer_id)
        logger.logger.info(f"AUTHORIZED_USER  real_id: {real_id}")
        if str(real_id) in self.TG_AUTHORIZED_USER_ID:
            return True
        else:
            logger.logger.info("USUARIO: %s NO AUTORIZADO", real_id)
            return False

    def resolve_id(self, fwd_from):
        try:
            real_id = get_peer_id(fwd_from.from_id)
            bot_group_t, peer_type = resolve_id(real_id)
            if peer_type == PeerChannel:
                logger.logger.info(f"resolve_id => real_id: {real_id}")
            elif peer_type == PeerUser:
                logger.logger.info(f"resolve_id => real_id: {real_id}")
            return real_id
        except Exception as e:
            logger.logger.error(f"resolve_id Exception: {e}")

    async def download_pending_messages(self):
        try:
            loaded_messages = self.pendingMessagesHandler.load_from_json()
            grouped = None
            # Group messages by user_id
            grouped_dict = {}
            for item in loaded_messages:
                user_id = str(item["user_id"])
                message = item["message"]

                if user_id in grouped_dict:
                    grouped_dict[user_id].append(message)
                else:
                    grouped_dict[user_id] = [message]

            logger.logger.info(
                f" [!!] download_pending_messages grouped_dict: {grouped_dict}"
            )

            for grouped in grouped_dict:
                logger.logger.info(
                    f" [!!] download_pending_messages grouped_dict: {grouped} => {grouped_dict[grouped]}"
                )

                messages = await self.client.get_messages(
                    int(grouped), ids=grouped_dict[grouped]
                )

                for message in messages:
                    asyncio.create_task(self.download_media_with_retries(message))

        except Exception as e:
            logger.logger.error(f"download_pending_messages Exception {grouped}: {e}")

    async def download_media_with_retries(self, event, retry_count=1, message=None):
        try:
            download_response = await self.download_media(event, message)
            logger.logger.info(
                f" [!!] download_media_with_retries download_response: [{download_response}] => [{message}]"
            )

            if isinstance(download_response["exception"], Exception):
                if retry_count < self.max_retries:
                    logger.logger.error(
                        f"Download failed, retrying... isinstance {retry_count} => [{download_response}]"
                    )
                    await self.download_media_with_retries(
                        event, retry_count + 1, download_response["message"]
                    )

        except Exception as e:
            if retry_count < self.max_retries:
                logger.logger.error(
                    f"Download failed, retrying... Attempt {retry_count} => {e}"
                )
                await self.download_media_with_retries(event, retry_count + 1)
            else:
                logger.logger.error(
                    f"Download failed after {self.max_retries} attempts => {e}"
                )

    async def download_media(self, event, message=None):
        try:
            if not message:
                message = await event.reply("Download in queue...")
            else:
                message = await message.edit("Download in queue, retrying... ")
                await asyncio.sleep(3)

            user_or_chat_id = (
                event.peer_id.user_id
                if hasattr(event.peer_id, "user_id")
                else event.peer_id.chat_id
                if hasattr(event.peer_id, "chat_id")
                else None
            )
            self.pendingMessagesHandler.add_pending_message(
                user_or_chat_id, event.id
            ) if user_or_chat_id is not None else None

            is_torrent_file = None

            if event.media and hasattr(event.media, "document"):
                is_torrent_file = self.is_torrent_file(event)
                if is_torrent_file:
                    logger.logger.info(
                        f"download_media => is_torrent_file: {is_torrent_file}"
                    )

                    download_response = await self.downloadDocumentAttributeFilename(
                        event, message
                    )

                    if isinstance(download_response["exception"], Exception):
                        logger.logger.info(
                            f"download_media is_torrent_file Exception: {download_response}"
                        )
                        return {
                            "exception": download_response["exception"],
                            "message": download_response["message"],
                        }

                    self.pendingMessagesHandler.remove_pending_message(
                        user_or_chat_id, event.id
                    )
                    return {
                        "exception": None,
                        "message": message,
                    }

            async with self.semaphore:
                message = await message.edit("Download in progress")
                if isinstance(event.media, MessageMediaDocument):
                    download_response = await self.downloadDocumentAttributeFilename(
                        event, message
                    )
                elif isinstance(event.media, MessageMediaPhoto):
                    download_response = await self.downloadMessageMediaPhoto(
                        event, message
                    )
                elif isinstance(event.media, MessageMediaWebPage):
                    download_response = await self.downloadMessageMediaWebPage(
                        event, message
                    )
                else:
                    download_response = await self.downloadLinks(event, message)
                if isinstance(download_response["exception"], Exception):
                    logger.logger.info(
                        f"download_media Exception if: [{download_response}]"
                    )
                    return {
                        "exception": download_response["exception"],
                        "message": download_response["message"],
                    }

                self.pendingMessagesHandler.remove_pending_message(
                    user_or_chat_id, event.id
                )
                return {
                    "exception": None,
                    "message": message,
                }
        except Exception as e:
            logger.logger.error(f"Exception 998: {e}")
            message = await message.edit(f"Exception 998: {e} ")
            return {
                "exception": e,
                "message": message,
            }

    async def get_group_name(self, chat_id):
        try:
            chat = await self.client.get_entity(chat_id)
            if hasattr(chat, "title"):
                return chat.title
            return None
        except Exception as e:
            return None

    async def downloadMessageMediaWebPage(self, event, message):
        try:
            logger.logger.info("downloadMessageMediaWebPage")
            await self.downloadLinks(event, message)
            return {
                "exception": None,
                "message": message,
            }
        except Exception as e:
            logger.logger.error(f"downloadMessageMediaWebPage Exception: {e}")
            message = await message.edit(f"Exception downloadMessageMediaWebPage: {e}")
            return {
                "exception": e,
                "message": message,
            }

    async def downloadMessageMediaPhoto(self, event, message):
        try:
            logger.logger.info("downloadMessageMediaPhoto")

            last_size = 0

            for size in event.media.photo.sizes:
                if hasattr(size, "size"):
                    logger.logger.info(f"Desired size:::: {size}")
                    last_size = size.size if size.size > last_size else last_size

                if hasattr(size, "sizes"):
                    logger.logger.info(f"Desired size IF: {size}")
                    last_size = size.sizes[-1]
                    break

            logger.logger.info(f"downloadMessageMediaPhoto last_size: {last_size}")
            download_response = await self.download(event, message, last_size)
            return {
                "exception": download_response["exception"],
                "message": download_response["message"],
            }

        except Exception as e:
            logger.logger.error(f"downloadMessageMediaPhoto Exception: {e}")
            message = await message.edit(f"Exception downloadMessageMediaPhoto: {e}")
            return {
                "exception": e,
                "message": message,
            }

    async def downloadDocumentAttributeFilename(self, event, message):
        try:
            download_response = await self.download(
                event, message, event.media.document.size
            )
            return {
                "exception": download_response["exception"],
                "message": download_response["message"],
            }

        except Exception as e:
            message = await message.edit(f"Exception download: {e}")
            return {"exception": e, "message": message}

    async def download(self, event, message, total_size):
        logger.logger.info(f"download: {message.id}")
        file_name = ""
        try:
            from_id = self.resolve_id(event.fwd_from)

            megabytes_total = total_size / 1024 / 1024
            download_start_time = time.time()
            self.utils.create_folders(self.PATH_TMP)

            message_text = self.templatesLanguage.template("MESSAGE_DOWNLOAD").format(
                path=self.PATH_TMP
            )
            message_text += self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_FROM_ID"
            ).format(from_id=from_id)
            message = await message.edit(message_text)

            if isinstance(event.media, MessageMediaDocument):
                for attr in event.media.document.attributes:
                    if isinstance(attr, DocumentAttributeFilename):
                        file_name = f"{attr.file_name}.tmp"
                        break

            loop = asyncio.get_event_loop()
            task = loop.create_task(
                self.client.download_media(
                    event.media,
                    file=os.path.join(self.PATH_TMP, file_name),
                    progress_callback=self.progress_callback(
                        message, event.id, from_id
                    ),
                )
            )
            logger.logger.info(
                f"download => task: {event.id} > {message.id} > [{from_id}] >> [{self.TG_DL_TIMEOUT}]"
            )

            downloaded_file = await asyncio.wait_for(task, timeout=self.TG_DL_TIMEOUT)

            logger.logger.info(f"download => downloaded_file: {downloaded_file}")

            # Check if the downloaded file ends with ".tmp" and remove it from the file name
            if downloaded_file.endswith(".tmp"):
                file_path = os.path.join(self.PATH_TMP, downloaded_file)
                os.rename(
                    file_path, file_path[:-4]
                )  # Remove the last 4 characters (".tmp")
                logger.logger.info(
                    f"File renamed: {downloaded_file} to {downloaded_file[:-4]}"
                )
                downloaded_file = downloaded_file[:-4]

            logger.logger.info(
                f"download => downloaded_file: {event.id} > [{downloaded_file}]"
            )

            downloaded_file = await self.moveFile(downloaded_file, from_id)

            logger.logger.info(
                f"download => finish moveFile: {event.id} > {downloaded_file}"
            )

            self.downloadFilesDB.add_download_files(
                from_id, event.id, message.id, downloaded_file
            )

            self.postProcess(downloaded_file)
            await self.unCompress(downloaded_file)

            # asyncio.create_task(extract_unrar("archivo.rar", "destino/", client, chat_id, message_id))

            logger.logger.info(
                f"download => finish unCompress: {event.id} {downloaded_file}"
            )

            end_time_short = time.strftime("%H:%M", time.localtime())
            logger.logger.info(f"File downloaded in: {downloaded_file}")
            download_end_time = time.time()
            elapsed_time_total = download_end_time - download_start_time
            total_speed = (
                megabytes_total / elapsed_time_total if elapsed_time_total > 0 else 0
            )

            logger.logger.info(
                f"download => speed: {elapsed_time_total} seconds, {downloaded_file}"
            )

            message_text = self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_FILE"
            ).format(downloaded_file=downloaded_file)
            message_text += self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_COMPLETED"
            ).format(elapsed_time=self.format_time(elapsed_time_total))
            message_text += self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_SPEED"
            ).format(speed=total_speed)
            message_text += self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_FROM_ID"
            ).format(from_id=from_id)
            message_text += self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_AT"
            ).format(end_time=end_time_short)

            message = await message.edit(f"{message_text}")

            return {
                "exception": None,
                "message": message,
            }

        except asyncio.TimeoutError as e:
            end_time_short = time.strftime("%H:%M", time.localtime())
            logger.logger.exception(f"Download TimeoutError Exception: {event.id}")
            self.TG_DL_TIMEOUT = self.TG_DL_TIMEOUT + (60 * 30)
            message_text = self.templatesLanguage.template("MESSAGE_TIMEOUT_EXCEEDED")
            message_text += self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_AT"
            ).format(end_time=end_time_short)
            message = await message.edit(message_text)
            return {
                "exception": e,
                "message": message,
            }

        except Exception as e:
            end_time_short = time.strftime("%H:%M", time.localtime())
            logger.logger.exception(f"Download Exception: {event.id} > {e}")
            message_text = self.templatesLanguage.template("MESSAGE_EXCEPTION")
            message_text += self.templatesLanguage.template(
                "MESSAGE_DOWNLOAD_AT"
            ).format(end_time=end_time_short)
            message = await message.edit(message_text)
            return {
                "exception": e,
                "message": message,
            }
            return e

    async def downloadLinks(self, event, message):
        try:
            logger.logger.info(f"downloadLinks => event.message: {event.message}")

            url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            urls = re.findall(url_pattern, event.message)

            tasks = []

            for url in urls:
                if any(yt in url for yt in self.YOUTUBE_LINKS_SUPPORTED):
                    task = self.youTubeDownloader(message, url)
                    tasks.append(task)
                elif all([urlparse(url).scheme, urlparse(url).netloc]):
                    task = self.download_url_file(message, url)
                    tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks)
            else:
                logger.logger.info(f"downloadLinks => NO ULRS: {urls}")
                await message.delete()
            return {
                "exception": None,
                "message": message,
            }
        except Exception as e:
            logger.logger.error(f"downloadLinks Exception: {e}")
            return {
                "exception": e,
                "message": message,
            }

    async def moveFile(self, file_path, from_id=None):
        try:
            logger.logger.info(f"moveFile file_path: {file_path}")
            logger.logger.info(f"moveFile from_id: {from_id}")
            final_path = None

            path_obj = Path(file_path)

            basename = path_obj.name
            filename = path_obj.stem
            extension = path_obj.suffix
            directory = path_obj.parent

            self.DEFAULT_PATH_EXTENSIONS = self.getConfigurationManager()
            self.GROUP_PATH = self.getConfigurationManager("GROUP_PATH")
            self.REGEX_PATH = self.getConfigurationManager("REGEX_PATH")

            self.SECTIONS = self.getConfigurationManagerAll()
            self.DownloadPathManager = DownloadPathManager(self.SECTIONS)

            if file_path.endswith(".torrent"):
                final_path = os.path.join(self.TG_DOWNLOAD_PATH_TORRENTS, basename)
            elif str(from_id) in self.GROUP_PATH:
                final_path = os.path.join(
                    self.CONFIG_MANAGER.get_value("GROUP_PATH", str(from_id)), basename
                )
            elif downloadPath := self.DownloadPathManager.getREGEXPATH(filename):
                final_path = os.path.join(downloadPath, basename)
            elif extension[1:] in self.DEFAULT_PATH_EXTENSIONS:
                final_path = os.path.join(
                    self.CONFIG_MANAGER.get_value("DEFAULT_PATH", extension[1:]),
                    basename,
                )
            else:
                final_path = os.path.join(self.PATH_COMPLETED, basename)

            directorio_base = Path(final_path).parent
            if os.path.exists(final_path):
                destination_filename = basename
                counter = 1
                while os.path.exists(
                    os.path.join(directorio_base, destination_filename)
                ):
                    destination_filename = f"{filename} ({counter}){extension}"
                    counter += 1
                final_path = os.path.join(directorio_base, destination_filename)

            self.utils.create_folders(directorio_base)
            final_path = shutil.move(file_path, final_path)
            logger.logger.info(f"shutil.move final_path: {final_path}")
            self.utils.change_owner_permissions(final_path)
            logger.logger.info(f"moveFile final_path: {final_path}")

            return final_path

        except Exception as e:
            logger.logger.error(f"moveFile Exception : {file_path} [{e}]")

    async def unCompress(self, file_path):
        try:
            file_name_with_extension = os.path.basename(file_path)
            file_name, file_extension = os.path.splitext(file_name_with_extension)

            logger.logger.info(
                f"unCompress path: [{file_path}] [{file_name_with_extension}] file_name:[{file_name}] file_extension:[{file_extension}]"
            )

            invalid_patterns = [
                r"\.part[0-9]+\.rar",
                r"\.part[0-9]+.*\.rar",
                r"\.zip\.[0-9]+",
                r"\.zip.*\.[0-9]+",
                r"\.z[0-9]+",
            ]

            for pattern in invalid_patterns:
                if re.search(pattern, file_name_with_extension, re.IGNORECASE):
                    return

            directorio_destino = os.path.join(
                os.path.dirname(file_path),
                os.path.splitext(os.path.basename(file_path))[0],
            )

            if self.ENABLED_UNRAR and file_name_with_extension.endswith(".rar"):
                logger.logger.info(
                    f"unCompress endswith rar: [{file_path}] [{file_name_with_extension}] file_name:[{file_name}] file_extension:[{file_extension}]"
                )

                self.utils.create_folders(directorio_destino)
                fileExtractor = FileExtractor()
                await fileExtractor.extract_unrar(file_path, directorio_destino)
                self.utils.change_owner_permissions(directorio_destino)

            elif self.ENABLED_UNZIP and file_name_with_extension.endswith(".zip"):
                logger.logger.info(
                    f"unCompress endswith zip: [{file_path}] [{file_name_with_extension}] file_name:[{file_name}] file_extension:[{file_extension}]"
                )

                self.utils.create_folders(directorio_destino)
                fileExtractor = FileExtractor()
                await fileExtractor.extract_unzip(file_path, directorio_destino)
                self.utils.change_owner_permissions(directorio_destino)

            return

        except Exception as e:
            logger.logger.error(f"unCompress Exception : {file_path} [{e}]")

    async def youTubeDownloader(self, message, text):
        try:
            logger.logger.info(f"youTubeDownloader => media: {message}")
            logger.logger.info(f'youTubeDownloader => text: "{text}"')
            logger.logger.info(f'youTubeDownloader => message.id: "{message.id}"')

            self.youtubeLinks[message.id] = text

            if self.YOUTUBE_SHOW_OPTION:
                button1 = Button.inline("Audio", data=f"{message.id},A")
                button2 = Button.inline("Video", data=f"{message.id},V")

                response = await message.edit(
                    "Downloading:", buttons=[button1, button2]
                )

                await asyncio.sleep(self.YOUTUBE_SHOW_OPTION_TIMEOUT)

            logger.logger.info(
                f"youTubeDownloader => self.youtubeLinks: {self.youtubeLinks} => {message.id}"
            )

            if message.id in self.youtubeLinks:
                removed_value = self.youtubeLinks.pop(int(message.id))
                if self.YOUTUBE_DEFAULT_DOWNLOAD.upper() == "VIDEO":
                    await message.edit("Downloading video")
                    await self.ytdownloader.downloadVideo(text, message)
                elif self.YOUTUBE_DEFAULT_DOWNLOAD.upper() == "AUDIO":
                    await message.edit("Downloading Audio")
                    await self.ytdownloader.downloadAudio(text, message)
                else:
                    await message.edit("Downloading video")
                    await self.ytdownloader.downloadVideo(text, message)

        except Exception as e:
            logger.logger.error(f"youTubeDownloader => Exception: {e}")
            await message.reply(f"Error: {e}")
            pass

    async def download_url_file(self, message, url):
        try:
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)

            download_start_time = time.time()

            response = requests.head(url, allow_redirects=True)
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type:
                logger.logger.info(f"download_url_file => NO DOWNLOADED LINK: {url}")
                await message.delete()

                return

            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file_path = os.path.join(self.PATH_LINKS, file_name)
                message = await message.edit(
                    self.templatesLanguage.template("MESSAGE_DOWNLOAD").format(
                        path=self.PATH_LINKS
                    )
                )
                self.utils.create_folders(self.PATH_LINKS)

                with open(file_path, "wb") as file:
                    file.write(response.content)

                    file_path = await self.moveFile(file_path)

                    self.utils.change_owner_permissions(file_path)
                    file_size = len(response.content) / 1024 / 1024
                    download_end_time = time.time()
                    elapsed_time_total = download_end_time - download_start_time
                    total_speed = (
                        file_size / elapsed_time_total if elapsed_time_total > 0 else 0
                    )
                    end_time_short = time.strftime("%H:%M", time.localtime())
                    f_elapsed_time_total = self.format_time(elapsed_time_total)

                    message_text = self.templatesLanguage.template(
                        "MESSAGE_DOWNLOAD_FILE"
                    ).format(downloaded_file=file_path)
                    message_text += self.templatesLanguage.template(
                        "MESSAGE_DOWNLOAD_FILE_SIZE"
                    ).format(file_size=file_size)
                    message_text += self.templatesLanguage.template(
                        "MESSAGE_DOWNLOAD_COMPLETED"
                    ).format(elapsed_time=f_elapsed_time_total)
                    message_text += self.templatesLanguage.template(
                        "MESSAGE_DOWNLOAD_SPEED"
                    ).format(speed=total_speed)
                    message_text += self.templatesLanguage.template(
                        "MESSAGE_DOWNLOAD_AT"
                    ).format(end_time=end_time_short)

                    message = await message.edit(f"{message_text}")

                    logger.logger.info(
                        f"download_url_file {url}. Status code: {response.status_code} => {file_path}"
                    )
                return file_path
            else:
                logger.logger.info(
                    f"download_url_file {url}. Status code: {response.status_code}"
                )
                await message.delete()

                return None
        except Exception as e:
            logger.logger.error(f"download_url_file {url}. {e}")
            await message.delete()

    async def commands(self, message):
        try:
            logger.logger.info(f"commands => message: {message}")
            logger.logger.info(f"commands => message: {message.message}")
            if self.AUTHORIZED_USER(message):
                process_command = self.command_handler.process_command(message)
                if process_command:
                    await message.respond(process_command)
            elif message.message == "/id":
                process_command = self.command_handler.process_command(message)
                await message.respond(process_command)

        except Exception as e:
            logger.logger.error(f"commands => Exception: {e}")

    def is_torrent_file(self, event):
        try:
            file_name = next((attr.file_name for attr in event.media.document.attributes if isinstance(attr, DocumentAttributeFilename)), None)  # fmt: skip

            logger.logger.info(f"is_torrent_file DocumentAttributeFilename: {file_name}")  # fmt: skip

            if not file_name:
                return False

            path_obj = Path(file_name)

            _basename = path_obj.name
            _filename = path_obj.stem
            _extension = path_obj.suffix
            _directory = path_obj.parent

            extension = _extension.split(".")[-1]

            if extension.lower() in self.ignored_extensions:
                return True

        except Exception as e:
            logger.logger.error(f"is_torrent_file Exception {e}")
            return False

    def format_time(self, seconds):
        try:
            total_seconds = float(seconds)

            integer_part = int(total_seconds)
            fractional_part = total_seconds - integer_part

            time_delta = timedelta(
                seconds=integer_part, milliseconds=fractional_part * 1000
            )
            time_parts = str(time_delta).split(", ")

            hours, minutes, rest = time_parts[0].split(":")
            seconds, milliseconds = rest.split(".")
            milliseconds = milliseconds[:3]

            HOUR = self.templatesLanguage.templateOneLine("HOUR")
            MINUTE = self.templatesLanguage.templateOneLine("MINUTE")
            SECOND = self.templatesLanguage.templateOneLine("SECOND")

            HOURS = self.templatesLanguage.templateOneLine("HOURS")
            MINUTES = self.templatesLanguage.templateOneLine("MINUTES")
            SECONDS = self.templatesLanguage.templateOneLine("SECONDS")

            time_parts = [
                f"{hours} {HOUR}{'s' * (int(hours) != 1)}" if int(hours) else "",
                f"{minutes} {MINUTE}{'s' * (int(minutes) != 1)}" if int(minutes) else "",
                f"{seconds} {SECONDS}",
                f"{milliseconds} ms" if milliseconds else "",
            ]  # fmt: skip

            formatted_time = " ".join(filter(None, time_parts))
            return formatted_time
        except Exception as e:
            logger.logger.error(f"format_time {seconds}. {e}")
            return seconds

    def progress_callback(self, message, event_id, from_id=None):
        async def callback(current, total):
            if not self.TG_PROGRESS_DOWNLOAD:
                return

            try:
                nonlocal last_percentage

                percentage = int(current / total * 100)
                if (
                    percentage <= 5
                    and percentage % 1 == 0
                    and percentage != last_percentage
                ) or (percentage % 10 == 0 and percentage != last_percentage):
                    speed = current / (time.time() - start_time) / (1024 * 1024)

                    megabytes_total = total / 1024 / 1024
                    message_text = self.templatesLanguage.template(
                        "PROGRESS_CALLBACK_PATH"
                    ).format(path=self.PATH_TMP)
                    if from_id:
                        message_text += self.templatesLanguage.template(
                            "MESSAGE_DOWNLOAD_FROM_ID"
                        ).format(from_id=from_id)
                    message_text += self.templatesLanguage.template(
                        "PROGRESS_CALLBACK_STARTING"
                    ).format(starting=_start_time)

                    message_text += self.templatesLanguage.template(
                        "PROGRESS_CALLBACK_PROGRESS"
                    ).format(
                        percentage=int(percentage), total=megabytes_total, speed=speed
                    )

                    await self.client.edit_message(
                        message.chat_id, message.id, message_text
                    )
                    last_percentage = percentage
                    if percentage % 10 == 0:
                        logger.logger.info(
                            f"Downloading... {event_id} > {message.id} >> {int(percentage)}% - Speed: {speed:.2f} MB/s"
                        )
            except Exception:
                return

        last_percentage = -1
        start_time = time.time()
        _start_time = time.strftime("%H:%M:%S", time.localtime())
        logger.logger.info(f"progress_callback started {message.id}.")
        return callback

    def create_directoryTmp(self, path):
        try:
            logger.logger.info(f"create_directory path: {path}")
            os.makedirs(path, exist_ok=True)
            if (
                hasattr(self, "PUID")
                and hasattr(self, "PGID")
                and self.PUID is not None
                and self.PGID is not None
            ):
                if os.path.exists(path):
                    os.chown(path, self.PUID, self.PGID)
            if os.path.exists(path):
                os.chmod(path, 0o777)
        except Exception as e:
            logger.logger.error(f"create_directory Exception : {path} [{e}]")

    def postProcess(self, path):
        try:
            logger.logger.info(f"postProcess path: {path}")
        except Exception as e:
            logger.logger.error(f"postProcess Exception : {path} [{e}]")

    def clearNameFolders(self, folderName):
        try:
            return folderName

            for i, char in enumerate(folderName):
                if char.isalnum():
                    return folderName[i:]
            return str(folderName)
        except Exception as e:
            logger.logger.error(f"clearNameFolders Exception: [{e}]")

    async def renameFilesReply(self, event):
        try:
            logger.logger.info(f"renameFilesReply => RENAME: {event}")
            message = event.original_update.message

            # Check if the message is a reply
            if message.reply_to:
                new_name = (event.message.message).replace("/rename", "").strip()
                reply = await event.reply(f"rename file to: {new_name}...")

                reply_to_msg_id = message.reply_to.reply_to_msg_id
                logger.logger.info(
                    f"The message is a reply to message ID {reply_to_msg_id}"
                )
                found_element = self.downloadFilesDB.get_download_file(reply_to_msg_id)

                if found_element:
                    logger.logger.info(
                        f"renameFilesReply => found_element: {found_element}"
                    )

                    original_filename = (
                        found_element["original_filename"]
                        if not found_element["new_filename"]
                        else found_element["new_filename"]
                    )

                    renameFilesReply = self.newFilenameRename(
                        original_filename, new_name
                    )

                    logger.logger.info(
                        f"renameFilesReply => newFilenameRename: {original_filename}, {renameFilesReply}"
                    )
                    if self.utils.rename_file(original_filename, renameFilesReply):
                        self.downloadFilesDB.update_download_files(
                            reply_to_msg_id, renameFilesReply
                        )
                        reply = await reply.edit(
                            f"rename file: {original_filename} to: {renameFilesReply}..."
                        )

        except Exception as e:
            logger.logger.exception(f"downloadLinks Exception: {e}")
            return e

    def newFilenameRename(self, original_filename, new_name):
        try:
            path_obj = Path(new_name)
            _basename = path_obj.name
            _filename = path_obj.stem
            _extension = path_obj.suffix
            _directory = path_obj.parent

            if os.path.sep in new_name:
                logger.logger.info("The string represents a directory.")

                new_filename = os.path.join("/download", _directory, _basename)

                return new_filename

            else:
                logger.logger.info("The string represents a file name.")

                path_obj = Path(original_filename)

                basename = path_obj.name
                filename = path_obj.stem
                extension = path_obj.suffix
                directory = path_obj.parent

                new_filename = os.path.join("/download", directory, _basename)
                logger.logger.info(f" new_filename: {new_filename}")
                return new_filename
        except Exception as e:
            logger.logger.exception(f"downloadLinks Exception: {e}")
            return None


if __name__ == "__main__":
    bot = TelegramBot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start())
