import asyncio
import os
from telethon import TelegramClient, events
from telethon import __version__ as telethon_version

from logger_config import LoggerConfig
from env_config import EnvConfig
from download_manager import DownloadManager
from config_manager import ConfigManager
from welcome_message import WelcomeMessage
from bot_versions import BotVersions
from telethon_utils import TelethonUtils
from keyboard_manager import KeyboardManager
from commands import Commands
from download_tracker import DownloadTracker
from resume_manager import ResumeManager
from pending_downloads_manager import PendingDownloadsManager
from youtube_downloader import YouTubeDownloader
from direct_downloader import DirectDownloader
from youtube_handler import YouTubeHandler
from torrent_magnet_handler import TorrentMagnetHandler
from file_browser_handler import FileBrowserHandler
from file_download_handler import FileDownloadHandler
from callback_router import CallbackRouter

VERSION = "4.0.15"


class TelethonDownloaderBot:
    def __init__(self):
        self.logger = LoggerConfig()

        try:
            self.env_config = EnvConfig(self.logger)
            if not self.env_config.validate_env():
                self.logger.error("Please set the environment variables API_ID, API_HASH, BOT_TOKEN, and AUTHORIZED_USER_ID.")
                exit(1)

            self.AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in self.env_config.AUTHORIZED_USER_ID.split(',')]
            self.bot = TelegramClient('bot', self.env_config.API_ID, self.env_config.API_HASH)

            os.makedirs(self.env_config.PATH_CONFIG, exist_ok=True)

            self.config_manager = ConfigManager(self.env_config.PATH_CONFIG, self.logger, self.env_config.PUID, self.env_config.PGID)
            self.download_manager = DownloadManager(self.env_config.BASE_DOWNLOAD_PATH, self.config_manager, self.logger, self.env_config, self.env_config.PUID, self.env_config.PGID, self.env_config.DOWNLOAD_PATH_TORRENTS)
            self.download_semaphore = asyncio.Semaphore(int(self.env_config.MAX_CONCURRENT_TASKS))
            self.telethon_utils = TelethonUtils(self.logger, self.config_manager)
            self.keyboard_manager = KeyboardManager(self.logger, self.env_config.BASE_DOWNLOAD_PATH)
            self.download_tracker = DownloadTracker(self.env_config.PATH_CONFIG, self.logger)
            self.welcome_message_generator = WelcomeMessage(BotVersions(VERSION, telethon_version, self.logger), self.env_config, self.logger, self.download_manager)

            downloaded_files = {}
            media_groups = {}

            self.commands_manager = Commands(VERSION, self.welcome_message_generator, self.download_tracker, self.download_manager, self.bot, self.keyboard_manager, self.config_manager, self.telethon_utils, self.logger)
            self.resume_manager = ResumeManager(self.bot, self.logger)

            self.file_download_handler = FileDownloadHandler(
                self.bot, self.download_manager, self.download_tracker,
                self.telethon_utils, self.env_config, self.keyboard_manager,
                self.download_semaphore, downloaded_files, media_groups, self.logger
            )

            self.pending_downloads_manager = PendingDownloadsManager(self.download_tracker, self.logger, self.file_download_handler)

            self.direct_downloader = DirectDownloader(
                self.env_config, self.logger, self.download_manager,
                self.file_download_handler._finalize_download_processing
            )

            self.youtube_handler = YouTubeHandler(self.bot, YouTubeDownloader(self.env_config), self.env_config, self.logger)

            self.torrent_magnet_handler = TorrentMagnetHandler(
                self.bot, self.env_config, self.download_manager,
                downloaded_files, self.file_download_handler._finalize_download_processing, self.logger
            )

            self.file_browser_handler = FileBrowserHandler(
                self.bot, self.keyboard_manager, self.download_manager,
                self.download_tracker, self.env_config, downloaded_files, media_groups, self.logger
            )

            # Wire cross-references: each handler needs the other after both are constructed.
            self.file_download_handler.torrent_magnet_handler = self.torrent_magnet_handler
            self.file_download_handler.file_browser_handler = self.file_browser_handler

            self.callback_router = CallbackRouter(
                self.file_download_handler, self.commands_manager,
                self.torrent_magnet_handler, self.file_browser_handler,
                self.pending_downloads_manager, self.logger
            )

            self._add_handlers()
            self.logger.info("Bot initialized.")
        except Exception as e:
            self.logger.error(f"Error during bot initialization: {e}")
            exit(1)

    def _add_handlers(self):
        au = self.AUTHORIZED_USER_IDS
        df = self.file_download_handler.downloaded_files
        cm = self.commands_manager

        self.bot.add_event_handler(
            self.file_download_handler.download_media,
            events.NewMessage(incoming=True, func=lambda e: (e.message.document or e.message.photo) and e.sender_id in au)
        )
        self.bot.add_event_handler(
            self.callback_router.route,
            events.CallbackQuery(func=lambda e: not e.data.startswith(b'yt_'))
        )
        self.bot.add_event_handler(
            self.file_browser_handler.handle_new_folder_name,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and any(df[m].get('waiting_for_folder_name') for m in df))
        )
        self.bot.add_event_handler(
            self._handle_text_commands,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and e.message.text.startswith('/'))
        )
        self.bot.add_event_handler(
            self._handle_add_path_new_folder_name,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and not e.message.text.startswith('/') and (e.sender_id in cm.active_add_extension_prompts or e.sender_id in cm.active_add_group_prompts))
        )
        self.bot.add_event_handler(
            cm.handle_extension_input,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and not e.message.text.startswith('/') and e.sender_id in cm.active_add_extension_prompts)
        )
        self.bot.add_event_handler(
            cm.handle_group_id_input,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and not e.message.text.startswith('/') and e.sender_id in cm.active_add_group_prompts)
        )
        self.bot.add_event_handler(
            self.torrent_magnet_handler.handle_magnet_link,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and e.message.text.startswith('magnet:?'))
        )
        self.bot.add_event_handler(
            self.direct_downloader.handle_direct_link,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and (e.message.text.startswith('http://') or e.message.text.startswith('https://')) and not ('youtube.com' in e.message.text or 'youtu.be' in e.message.text))
        )
        self.bot.add_event_handler(
            self.youtube_handler.handle_youtube_link,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and ('youtube.com' in e.message.text or 'youtu.be' in e.message.text))
        )
        self.bot.add_event_handler(
            self.youtube_handler.handle_youtube_choice,
            events.CallbackQuery(pattern=b'yt_')
        )
        self.bot.add_event_handler(
            self.torrent_magnet_handler.handle_new_category_name,
            events.NewMessage(incoming=True, func=lambda e: e.sender_id in au and e.message.text and any(df[m].get('waiting_for_category_name') for m in df))
        )

    async def _handle_text_commands(self, event):
        message_text = event.message.text
        sender_id = event.sender_id
        if message_text.startswith('/'):
            command_name = message_text.split(' ')[0]
            await self.commands_manager.execute_command(command_name, event)
        elif sender_id in self.commands_manager.active_rename_prompts:
            await self.commands_manager.handle_new_rename_input(event)

    async def _handle_add_path_new_folder_name(self, event):
        sender_id = event.sender_id
        prompt_info = (
            self.commands_manager.active_add_extension_prompts.get(sender_id) or
            self.commands_manager.active_add_group_prompts.get(sender_id)
        )
        if not prompt_info or prompt_info.get('state') != 'waiting_for_new_folder_name':
            return

        new_folder_name = event.text.strip()
        current_dir = prompt_info.get('current_dir', self.env_config.BASE_DOWNLOAD_PATH)
        new_folder_path = os.path.join(current_dir, new_folder_name)
        message_id = prompt_info.get('browser_message_id')

        try:
            os.makedirs(new_folder_path, exist_ok=True)
            self.download_manager._apply_permissions_and_ownership(new_folder_path)
            prompt_info['state'] = 'waiting_for_path'
            prompt_info['current_dir'] = new_folder_path
            text, buttons = await self.keyboard_manager.send_directory_browser(message_id, new_folder_path, page=0)
            await self.bot.edit_message(event.chat_id, message_id, text, buttons=buttons)
            await event.delete()
        except Exception as e:
            self.logger.error(f"Error creating new folder during add path: {e}")
            await event.reply(f"Error creating folder: {e}")

    async def run(self):
        try:
            await self.bot.start(bot_token=self.env_config.BOT_TOKEN)
            self.welcome_message_generator.log_welcome_message()
            try:
                await self.bot.send_message(self.AUTHORIZED_USER_IDS[0], self.welcome_message_generator.get_message())
                pending_downloads = self.download_tracker.get_pending_downloads()
                await self.resume_manager.ask_to_resume(pending_downloads, self.AUTHORIZED_USER_IDS[0])
            except Exception as e:
                self.logger.error(f"Error sending start message: {e}")
            await self.bot.run_until_disconnected()
        except Exception as e:
            self.logger.error(f"Unhandled exception in run: {e}")


if __name__ == "__main__":
    bot_instance = TelethonDownloaderBot()
    asyncio.run(bot_instance.run())
