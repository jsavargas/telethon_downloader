from telethon import TelegramClient, events
import os
import asyncio
import time
from logger_config import LoggerConfig
from progress_bar import ProgressBar
from download_summary import DownloadSummary
from env_config import EnvConfig
from download_manager import DownloadManager
from config_manager import ConfigManager
from welcome_message import WelcomeMessage
from bot_versions import BotVersions
from telethon import __version__ as telethon_version
from telethon_utils import TelethonUtils

VERSION = "5.0.0-r5"

class TelethonDownloaderBot:
    def __init__(self):
        self.logger = LoggerConfig(__name__).get_logger()

        self.env_config = EnvConfig()

        if not self.env_config.validate_env():
            self.logger.error("Please set the environment variables API_ID, API_HASH, BOT_TOKEN, and AUTHORIZED_USER_ID.")
            exit(1)

        self.API_ID = self.env_config.API_ID
        self.API_HASH = self.env_config.API_HASH
        self.BOT_TOKEN = self.env_config.BOT_TOKEN
        self.AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in self.env_config.AUTHORIZED_USER_ID.split(',')]

        self.bot = TelegramClient('bot', self.API_ID, self.API_HASH)

        self.config_manager = ConfigManager(self.env_config.PATH_CONFIG, self.logger, self.env_config.PUID, self.env_config.PGID)
        self.download_manager = DownloadManager(self.env_config.BASE_DOWNLOAD_PATH, self.config_manager, self.logger, self.env_config.PUID, self.env_config.PGID, self.env_config.DOWNLOAD_PATH_TORRENTS)
        self.download_semaphore = asyncio.Semaphore(int(self.env_config.MAX_CONCURRENT_TASKS))
        self.welcome_message_generator = WelcomeMessage(BotVersions(VERSION, telethon_version), self.env_config, self.logger, self.download_manager)

        self._add_handlers()

    def _add_handlers(self):
        self.bot.add_event_handler(self.download_media, events.NewMessage(incoming=True, func=lambda e: (e.message.document or e.message.photo) and e.sender_id in self.AUTHORIZED_USER_IDS))
        self.bot.add_event_handler(self.start_command, events.NewMessage(pattern='/start', incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS))

    async def download_media(self, event):
        message = event.message

        self.logger.info(f"message:::: {message}")

        file_info = TelethonUtils.get_file_info(message)
        file_extension = TelethonUtils.get_file_extension(message)
        origin_group = TelethonUtils.get_origin_group(message)
        channel_id = TelethonUtils.get_channel_id(message)

        target_download_dir, final_destination_dir = self.download_manager.get_download_dirs(file_extension, origin_group, channel_id)

        initial_message = await message.reply(f"Downloading {file_info}...")
        start_time = time.time()

        file_size = TelethonUtils.get_file_size(message)

        progress_bar = None
        if self.env_config.PROGRESS_DOWNLOAD.lower() == 'true':
            progress_bar = ProgressBar(initial_message, file_info, self.logger, final_destination_dir, file_size, start_time, origin_group, int(self.env_config.PROGRESS_STATUS_SHOW), channel_id)

        if channel_id:
            log_message_chat_id = f"Channel ID: {channel_id}"
        else:
            log_message_chat_id = f"User ID: {origin_group}"
        self.logger.info(f"Downloading of {file_info} from {log_message_chat_id}")
        async with self.download_semaphore:
            self.logger.info(f"Starting download of {file_info} from {log_message_chat_id}")
            try:
                if progress_bar:
                    downloaded_file_path = await self.bot.download_media(message, file=target_download_dir, progress_callback=progress_bar.progress_callback)
                else:
                    downloaded_file_path = await self.bot.download_media(message, file=target_download_dir)
                end_time = time.time()
                
                # Move file to completed directory
                final_file_path = self.download_manager.move_to_completed(downloaded_file_path, final_destination_dir)

                self.logger.info(f"Finished download of {file_info} to {final_file_path}")
                
                # Add a small delay to ensure the last progress update is sent
                await asyncio.sleep(0.5)

                summary = DownloadSummary(message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, channel_id)
                summary_text = summary.generate_summary()
                await initial_message.edit(summary_text)
            except Exception as e:
                self.logger.error(f"Error downloading {file_info}: {e}")
                await initial_message.edit(f"Error downloading {file_info}: {e}")

    async def start_command(self, event):
        await event.reply("Hello! Send me a document and I will download it.")

    async def run(self):
        await self.bot.start(bot_token=self.BOT_TOKEN)
        self.welcome_message_generator.log_welcome_message()
        try:
            await self.bot.send_message(self.AUTHORIZED_USER_IDS[0], self.welcome_message_generator.get_message())
        except Exception as e:
            self.logger.error(f"Error sending start message to authorized user: {e}")
        await self.bot.run_until_disconnected()

if __name__ == "__main__":
    bot_instance = TelethonDownloaderBot()
    asyncio.run(bot_instance.run())