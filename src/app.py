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
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
from telethon_utils import TelethonUtils
from urllib.parse import quote, unquote
from keyboard_manager import KeyboardManager

VERSION = "5.0.0-r5"

class TelethonDownloaderBot:
    def __init__(self):
        self.logger = LoggerConfig(__name__).get_logger()
        self.env_config = None
        self.API_ID = None
        self.API_HASH = None
        self.BOT_TOKEN = None
        self.AUTHORIZED_USER_IDS = None
        self.bot = None
        self.config_manager = None
        self.download_manager = None
        self.download_semaphore = None
        self.welcome_message_generator = None
        self.downloaded_files = {}
        self.telethon_utils = None
        self.keyboard_manager = None

        try:
            self.env_config = EnvConfig(self.logger)
            self.logger.info("EnvConfig initialized.")

            if not self.env_config.validate_env():
                self.logger.error("Please set the environment variables API_ID, API_HASH, BOT_TOKEN, and AUTHORIZED_USER_ID.")
                exit(1)
            self.logger.info("Environment variables validated.")

            self.API_ID = self.env_config.API_ID
            self.API_HASH = self.env_config.API_HASH
            self.BOT_TOKEN = self.env_config.BOT_TOKEN
            self.AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in self.env_config.AUTHORIZED_USER_ID.split(',')]
            self.logger.info("API credentials and authorized users set.")

            self.bot = TelegramClient('bot', self.API_ID, self.API_HASH)
            self.logger.info("TelegramClient initialized.")

            self.config_manager = ConfigManager(self.env_config.PATH_CONFIG, self.logger, self.env_config.PUID, self.env_config.PGID)
            self.logger.info("ConfigManager initialized.")

            self.download_manager = DownloadManager(self.env_config.BASE_DOWNLOAD_PATH, self.config_manager, self.logger, self.env_config.PUID, self.env_config.PGID, self.env_config.DOWNLOAD_PATH_TORRENTS)
            self.logger.info("DownloadManager initialized.")

            self.download_semaphore = asyncio.Semaphore(int(self.env_config.MAX_CONCURRENT_TASKS))
            self.logger.info("Download semaphore initialized.")

            self.welcome_message_generator = WelcomeMessage(BotVersions(VERSION, telethon_version, self.logger), self.env_config, self.logger, self.download_manager)
            self.logger.info("WelcomeMessageGenerator initialized.")

            self.downloaded_files = {}
            self.logger.info("Downloaded files dictionary initialized.")

            self.telethon_utils = TelethonUtils(self.logger)
            self.logger.info("TelethonUtils initialized.")

            self.keyboard_manager = KeyboardManager(self.logger, self.env_config.BASE_DOWNLOAD_PATH)
            self.logger.info("KeyboardManager initialized.")

            self._add_handlers()
            self.logger.info("Event handlers added.")
        except Exception as e:
            self.logger.error(f"Error during bot initialization: {e}")
            exit(1)

    def _add_handlers(self):
        try:
            self.bot.add_event_handler(self.download_media, events.NewMessage(incoming=True, func=lambda e: (e.message.document or e.message.photo) and e.sender_id in self.AUTHORIZED_USER_IDS))
            self.bot.add_event_handler(self.start_command, events.NewMessage(pattern='/start', incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS))
            self.bot.add_event_handler(self.handle_callback_query, events.CallbackQuery)
            self.bot.add_event_handler(self.handle_new_folder_name, events.NewMessage(incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS and e.message.text and any(self.downloaded_files[msg_id].get('waiting_for_folder_name', False) for msg_id in self.downloaded_files)))
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

                    self.downloaded_files[message.id] = {
                        'file_path': final_file_path,
                        'current_dir': self.env_config.BASE_DOWNLOAD_PATH, # Start navigation from base download path
                        'summary_text': summary_text
                    }

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
                    self.downloaded_files[message_id]['browser_chat_id'] = event.chat_id
                    self.downloaded_files[message_id]['browser_message_id'] = event.message_id # This is the message with the buttons
                    if self.keyboard_manager:
                        summary_text = file_info.get('summary_text', "")
                        text, buttons = await self.keyboard_manager.send_directory_browser(message_id, file_info['current_dir'], summary_text=summary_text)
                        await event.edit(text, buttons=buttons)
                    else:
                        await event.answer("Keyboard manager not initialized.")
            elif action == 'cancel':
                if message_id in self.downloaded_files:
                    summary_text = self.downloaded_files[message_id].get('summary_text', "Download operation cancelled.")
                    del self.downloaded_files[message_id]
                    await event.edit(summary_text, buttons=None)
                else:
                    await event.answer("File information not found.")
            elif action == 'new':
                if message_id in self.downloaded_files:
                    self.downloaded_files[message_id]['waiting_for_folder_name'] = True
                    self.downloaded_files[message_id]['browser_message_id'] = event.message_id
                    summary_text = self.downloaded_files[message_id].get('summary_text', "")
                    await event.edit(f"{summary_text}\n\nPlease send the name for the new folder.")
                else:
                    await event.answer("File information not found.")
            elif action == 'dir':
                selected_dir_name = unquote(parts[2])
                page = int(parts[3])
                if message_id in self.downloaded_files:
                    current_base_dir = self.downloaded_files[message_id]['current_dir']
                    new_full_path = os.path.join(current_base_dir, selected_dir_name)
                    self.downloaded_files[message_id]['current_dir'] = new_full_path # Update stored current_dir
                    if self.keyboard_manager:
                        text, buttons = await self.keyboard_manager.send_directory_browser(message_id, new_full_path, page=0)
                        await event.edit(text, buttons=buttons)
                    else:
                        await event.answer("Keyboard manager not initialized.")
            elif action == 'nav':
                nav_action = parts[2]
                # current_dir from callback data is the directory *before* the navigation action
                # We need to get the current_dir from self.downloaded_files for consistency
                current_dir_from_state = self.downloaded_files[message_id]['current_dir']
                page = int(parts[4])

                if message_id in self.downloaded_files:
                    if nav_action == 'next':
                        page += 1
                        self.downloaded_files[message_id]['current_dir'] = current_dir_from_state # Ensure consistency
                    elif nav_action == 'back':
                        page -= 1
                        self.downloaded_files[message_id]['current_dir'] = current_dir_from_state # Ensure consistency
                    elif nav_action == 'up':
                        new_current_dir = os.path.dirname(current_dir_from_state)
                        self.downloaded_files[message_id]['current_dir'] = new_current_dir
                        page = 0 # Reset page when going up
                    elif nav_action == 'this':
                        file_info = self.downloaded_files[message_id]
                        file_path = file_info['file_path']
                        destination_dir = current_dir_from_state
                        summary_text = file_info.get('summary_text', "")
                        new_file_path = self.download_manager.move_file(file_path, destination_dir)
                        if new_file_path:
                            await event.edit(f"{summary_text}\n\nFile moved successfully to {new_file_path}", buttons=None)
                            del self.downloaded_files[message_id]
                        else:
                            await event.edit(f"{summary_text}\n\nError moving file.", buttons=None)
                        return
                    
                    # Use the updated current_dir from state for sending the browser
                    if self.keyboard_manager:
                        text, buttons = await self.keyboard_manager.send_directory_browser(message_id, self.downloaded_files[message_id]['current_dir'], page)
                        await event.edit(text, buttons=buttons)
                    else:
                        await event.answer("Keyboard manager not initialized.")
                else:
                    await event.answer("File information not found.")

            await event.answer()
        except Exception as e:
            self.logger.error(f"Unhandled exception in handle_callback_query: {e}")
            await event.answer(f"Error processing callback: {e}")

    

    async def handle_new_folder_name(self, event):
        try:
            # Find the message ID that is waiting for a folder name
            target_message_id = None
            for msg_id, file_info in self.downloaded_files.items():
                if file_info.get('waiting_for_folder_name', False):
                    target_message_id = msg_id
                    break

            if target_message_id is None:
                return # Not waiting for a folder name

            new_folder_name = event.message.text
            current_dir = self.downloaded_files[target_message_id]['current_dir']
            new_folder_path = os.path.join(current_dir, new_folder_name)
            browser_message_id = self.downloaded_files[target_message_id].get('browser_message_id', None)
            browser_chat_id = self.downloaded_files[target_message_id].get('browser_chat_id', None)

            os.makedirs(new_folder_path, exist_ok=True)
            self.download_manager._apply_permissions_and_ownership(new_folder_path)
            self.downloaded_files[target_message_id]['waiting_for_folder_name'] = False

            # Move the file to the new folder
            file_info = self.downloaded_files[target_message_id]
            file_path = file_info['file_path']
            new_file_path = self.download_manager.move_file(file_path, new_folder_path)

            if new_file_path:
                summary_text = self.downloaded_files[target_message_id].get('summary_text', "")
                await self.bot.edit_message(browser_chat_id, browser_message_id, f"{summary_text}\n\nFolder '{new_folder_name}' created and file moved successfully to {new_file_path}", buttons=None)
                del self.downloaded_files[target_message_id]
            else:
                await event.reply(f"Folder '{new_folder_name}' created, but there was an error moving the file.")

            # Refresh the directory browser
            if browser_message_id and browser_chat_id:
                self.logger.info(f"Refreshing browser for message {target_message_id}")
        except Exception as e:
            self.logger.error(f"Error creating new folder: {e}")
            await event.reply(f"Error creating folder: {e}")

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