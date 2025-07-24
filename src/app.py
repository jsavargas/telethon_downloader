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
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup

VERSION = "5.0.0-r5"

class TelethonDownloaderBot:
    def __init__(self):
        self.logger = LoggerConfig(__name__).get_logger()

        try:
            self.env_config = EnvConfig(self.logger)

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
            self.welcome_message_generator = WelcomeMessage(BotVersions(VERSION, telethon_version, self.logger), self.env_config, self.logger, self.download_manager)
            self.downloaded_files = {}
            self.telethon_utils = TelethonUtils(self.logger)

            self._add_handlers()
        except Exception as e:
            self.logger.error(f"Error during bot initialization: {e}")
            exit(1)

    def _add_handlers(self):
        try:
            self.bot.add_event_handler(self.download_media, events.NewMessage(incoming=True, func=lambda e: (e.message.document or e.message.photo) and e.sender_id in self.AUTHORIZED_USER_IDS))
            self.bot.add_event_handler(self.start_command, events.NewMessage(pattern='/start', incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS))
            self.bot.add_event_handler(self.handle_callback_query, events.CallbackQuery)
        except Exception as e:
            self.logger.error(f"Error adding event handlers: {e}")

    async def download_media(self, event):
        try:
            message = event.message

            self.logger.info(f"message:::: {message}")

            file_info = self.telethon_utils.get_file_info(message)
            file_extension = self.telethon_utils.get_file_extension(message)
            origin_group = self.telethon_utils.get_origin_group(message)
            channel_id = self.telethon_utils.get_channel_id(message)

            target_download_dir, final_destination_dir = self.download_manager.get_download_dirs(file_extension, origin_group, channel_id)

            initial_message = await message.reply(f"Downloading {file_info}...")
            start_time = time.time()

            file_size = self.telethon_utils.get_file_size(message)

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
                    media_to_download = None
                    if message.document:
                        media_to_download = message.document
                    elif message.photo:
                        media_to_download = message.photo

                    if media_to_download:
                        if progress_bar:
                            downloaded_file_path = await self.bot.download_media(media_to_download, file=target_download_dir, progress_callback=progress_bar.progress_callback)
                        else:
                            downloaded_file_path = await self.bot.download_media(media_to_download, file=target_download_dir)
                    else:
                        self.logger.error(f"No downloadable media found in message {message.id}")
                        await initial_message.edit(f"Error: No downloadable media found in message.")
                        return
                    end_time = time.time()
                    
                    # Move file to completed directory
                    final_file_path = self.download_manager.move_to_completed(downloaded_file_path, final_destination_dir)

                    self.downloaded_files[message.id] = {
                        'file_path': final_file_path,
                        'current_dir': self.env_config.BASE_DOWNLOAD_PATH # Start navigation from base download path
                    }

                    self.logger.info(f"Finished download of {file_info} to {final_file_path}")
                    
                    # Add a small delay to ensure the last progress update is sent
                    await asyncio.sleep(0.5)

                    summary = DownloadSummary(message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, channel_id)
                    summary_text = summary.generate_summary()
                    buttons = summary.get_buttons()
                    try:
                        await initial_message.edit(summary_text, buttons=buttons.rows)
                    except Exception as edit_error:
                        self.logger.error(f"Error editing message with buttons for {file_info}: {edit_error}")
                        await initial_message.edit(f"Download completed, but error displaying buttons: {edit_error}")
                except Exception as e:
                    self.logger.error(f"Error downloading {file_info}: {e}")
                    await initial_message.edit(f"Error downloading {file_info}: {e}")
        except Exception as e:
            self.logger.error(f"Unhandled exception in download_media: {e}")

    async def handle_callback_query(self, event):
        try:
            data = event.data.decode('utf-8')
            self.logger.info(f"Callback data received: {data}")
            parts = data.split('_')
            self.logger.info(f"Callback parts: {parts}")
            action = parts[0]
            message_id = int(parts[1])

            if action == 'move':
                if message_id in self.downloaded_files:
                    file_info = self.downloaded_files[message_id]
                    await self._send_directory_browser(event, message_id, file_info['current_dir'])
                else:
                    await event.answer("File information not found.")
            elif action == 'cancel':
                if message_id in self.downloaded_files:
                    del self.downloaded_files[message_id]
                    await event.edit("Download operation cancelled.")
                else:
                    await event.answer("File information not found.")
            elif action == 'dir':
                selected_dir_name = parts[2]
                if message_id in self.downloaded_files:
                    current_base_dir = self.downloaded_files[message_id]['current_dir']
                    new_full_path = os.path.join(current_base_dir, selected_dir_name)
                    self.downloaded_files[message_id]['current_dir'] = new_full_path
                    await self._send_directory_browser(event, message_id, new_full_path, page=0)
                else:
                    await event.answer("File information not found.")
            elif action == 'nav':
                nav_action = parts[2]
                current_dir = parts[3]
                page = int(parts[4])
                if message_id in self.downloaded_files:
                    if nav_action == 'next':
                        page += 1
                    elif nav_action == 'back':
                        page -= 1
                    elif nav_action == 'up':
                        # current_dir already contains the parent path from the button data
                        page = 0 # Reset page when going up
                    elif nav_action == 'this':
                        file_info = self.downloaded_files[message_id]
                        file_path = file_info['file_path']
                        destination_dir = current_dir
                        await self._move_file(event, message_id, file_path, destination_dir)
                        return
                    await self._send_directory_browser(event, message_id, current_dir, page)
                else:
                    await event.answer("File information not found.")

            await event.answer()
        except Exception as e:
            self.logger.error(f"Unhandled exception in handle_callback_query: {e}")
            await event.answer(f"Error processing callback: {e}")

    async def _send_directory_browser(self, event, message_id, current_dir, page=0):
        try:
            all_items = os.listdir(current_dir)
            self.logger.info(f"Items in {current_dir}: {all_items}")
            dirs = [d for d in all_items if os.path.isdir(os.path.join(current_dir, d))]
            self.logger.info(f"Directories in {current_dir}: {dirs}")
            dirs.sort()

            items_per_page = 4
            total_pages = (len(dirs) + items_per_page - 1) // items_per_page
            
            start_index = page * items_per_page
            end_index = start_index + items_per_page
            current_page_dirs = dirs[start_index:end_index]

            buttons = []
            for i in range(0, len(current_page_dirs), 2):
                row = []
                row.append(KeyboardButtonCallback(current_page_dirs[i], data=f"dir_{message_id}_{current_page_dirs[i]}".encode('utf-8')))
                if i + 1 < len(current_page_dirs):
                    row.append(KeyboardButtonCallback(current_page_dirs[i+1], data=f"dir_{message_id}_{current_page_dirs[i+1]}".encode('utf-8')))

            nav_buttons = []
            if current_dir != self.env_config.BASE_DOWNLOAD_PATH:
                nav_buttons.append(KeyboardButtonCallback("Up", data=f"nav_{message_id}_up_{os.path.dirname(current_dir)}".encode('utf-8')))
            if page > 0:
                nav_buttons.append(KeyboardButtonCallback("Back", data=f"nav_{message_id}_back_{current_dir}_{page}".encode('utf-8')))
            nav_buttons.append(KeyboardButtonCallback("This", data=f"nav_{message_id}_this_{current_dir}".encode('utf-8')))
            if page < total_pages - 1:
                nav_buttons.append(KeyboardButtonCallback("Next", data=f"nav_{message_id}_next_{current_dir}_{page}".encode('utf-8')))
            buttons.append(nav_buttons)

            buttons.append([KeyboardButtonCallback("Cancel", data=f"cancel_{message_id}".encode('utf-8'))])

            text = f"""Current Directory: {current_dir}
Page: {page + 1}/{total_pages if total_pages > 0 else 1}"""
            await event.edit(text, buttons=buttons)

        except Exception as e:
            self.logger.error(f"Error sending directory browser: {e}")
            await event.answer(f"Error: {e}")

    async def _move_file(self, event, message_id, file_path, destination_dir):
        try:
            file_name = os.path.basename(file_path)
            new_file_path = os.path.join(destination_dir, file_name)
            os.rename(file_path, new_file_path)
            del self.downloaded_files[message_id]
            await event.edit_message(f"File moved successfully to {new_file_path}")
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            await event.answer(f"Error moving file: {e}")

    async def start_command(self, event):
        try:
            await event.reply("Hello! Send me a document and I will download it.")
        except Exception as e:
            self.logger.error(f"Error in start_command: {e}")

    async def run(self):
        try:
            await self.bot.start(bot_token=self.BOT_TOKEN)
            self.welcome_message_generator.log_welcome_message()
            try:
                await self.bot.send_message(self.AUTHORIZED_USER_IDS[0], self.welcome_message_generator.get_message())
            except Exception as e:
                self.logger.error(f"Error sending start message to authorized user: {e}")
            await self.bot.run_until_disconnected()
        except Exception as e:
            self.logger.error(f"Unhandled exception in run: {e}")

if __name__ == "__main__":
    bot_instance = TelethonDownloaderBot()
    asyncio.run(bot_instance.run())