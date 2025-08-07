from telethon import TelegramClient, events
from telethon.tl.types import Message
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
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup, KeyboardButton
from telethon_utils import TelethonUtils
from urllib.parse import quote, unquote
from keyboard_manager import KeyboardManager
from commands import Commands
from download_tracker import DownloadTracker
from resume_manager import ResumeManager
from pending_downloads_manager import PendingDownloadsManager
from youtube_downloader import YouTubeDownloader
from direct_downloader import DirectDownloader
import re

VERSION = "4.0.10-r11"

class TelethonDownloaderBot:
    def __init__(self):
        self.logger = LoggerConfig()
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
        self.youtube_downloader = None
        self.active_youtube_prompts = {}
        self.download_type = None

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

            os.makedirs(self.env_config.PATH_CONFIG, exist_ok=True)
            self.logger.info(f"Ensured config directory exists: {self.env_config.PATH_CONFIG}")

            self.download_manager = DownloadManager(self.env_config.BASE_DOWNLOAD_PATH, self.config_manager, self.logger, self.env_config, self.env_config.PUID, self.env_config.PGID, self.env_config.DOWNLOAD_PATH_TORRENTS)
            self.logger.info("DownloadManager initialized.")

            self.download_semaphore = asyncio.Semaphore(int(self.env_config.MAX_CONCURRENT_TASKS))
            self.logger.info("Download semaphore initialized.")

            self.welcome_message_generator = WelcomeMessage(BotVersions(VERSION, telethon_version, self.logger), self.env_config, self.logger, self.download_manager)
            self.logger.info("WelcomeMessageGenerator initialized.")

            self.downloaded_files = {}
            self.download_cancellation_flags = {}
            self.active_downloads = {}
            self.logger.info("Downloaded files dictionary initialized.")

            self.telethon_utils = TelethonUtils(self.logger, self.config_manager)
            self.logger.info("TelethonUtils initialized.")

            self.keyboard_manager = KeyboardManager(self.logger, self.env_config.BASE_DOWNLOAD_PATH)
            self.logger.info("KeyboardManager initialized.")

            self.download_tracker = DownloadTracker(self.env_config.PATH_CONFIG, self.logger)
            self.logger.info("DownloadTracker initialized.")

            self.commands_manager = Commands(VERSION, self.welcome_message_generator, self.download_tracker, self.download_manager, self.bot, self.logger)
            self.logger.info("Commands manager initialized.")

            self.resume_manager = ResumeManager(self.bot, self.logger)
            self.logger.info("ResumeManager initialized.")

            self.pending_downloads_manager = PendingDownloadsManager(self.download_tracker, self.logger, self)
            self.logger.info("PendingDownloadsManager initialized.")

            self.youtube_downloader = YouTubeDownloader(self.env_config)
            self.logger.info("YouTubeDownloader initialized.")

            self.direct_downloader = DirectDownloader(self.env_config, self.logger, self.download_manager, self._finalize_download_processing)
            self.logger.info("DirectDownloader initialized.")

            self._add_handlers()
            self.logger.info("Event handlers added.")
        except Exception as e:
            self.logger.error(f"Error during bot initialization: {e}")
            exit(1)

    def _add_handlers(self):
        try:
            self.bot.add_event_handler(self.download_media, events.NewMessage(incoming=True, func=lambda e: (e.message.document or e.message.photo) and e.sender_id in self.AUTHORIZED_USER_IDS))
            self.bot.add_event_handler(self.handle_callback_query, events.CallbackQuery(func=lambda e: not e.data.startswith(b'yt_')))
            self.bot.add_event_handler(self.handle_new_folder_name, events.NewMessage(incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS and e.message.text and any(self.downloaded_files[msg_id].get('waiting_for_folder_name', False) for msg_id in self.downloaded_files)))
            self.bot.add_event_handler(self.handle_text_commands, events.NewMessage(incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS and e.message.text and e.message.text.startswith('/')))
            self.bot.add_event_handler(self.handle_magnet_link, events.NewMessage(incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS and e.message.text and e.message.text.startswith('magnet:?')))
            self.bot.add_event_handler(self.handle_direct_link, events.NewMessage(incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS and e.message.text and (e.message.text.startswith('http://') or e.message.text.startswith('https://')) and not ("youtube.com" in e.message.text or "youtu.be" in e.message.text)))
            self.bot.add_event_handler(self.handle_youtube_link, events.NewMessage(incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS and e.message.text and ("youtube.com" in e.message.text or "youtu.be" in e.message.text)))
            self.bot.add_event_handler(self.handle_youtube_choice, events.CallbackQuery(pattern=b'yt_'))
            self.bot.add_event_handler(self.handle_new_category_name, events.NewMessage(incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS and e.message.text and any(self.downloaded_files[msg_id].get('waiting_for_category_name', False) for msg_id in self.downloaded_files)))

        except Exception as e:
            self.logger.error(f"Error adding event handlers: {e}")

    async def _start_timeout_task(self, prompt_message, url):
        prompt_id = prompt_message.id
        self.active_youtube_prompts[prompt_id] = {"url": url, "event": prompt_message}
        await asyncio.sleep(self.env_config.YOUTUBE_TIMEOUT_OPTION)
        if prompt_id in self.active_youtube_prompts:
            await self._handle_youtube_timeout(prompt_id)

    async def _handle_youtube_timeout(self, prompt_id):
        self.logger.info(f"YouTube prompt {prompt_id} timed out.")
        prompt_context = self.active_youtube_prompts.pop(prompt_id, None)
        if not prompt_context: return

        event = prompt_context["event"]
        url = prompt_context["url"]
        
        await event.edit(f"Timed out. Defaulting to first video, {self.env_config.YOUTUBE_DEFAULT_DOWNLOAD} format.")
        await self._perform_youtube_download(event, url, self.env_config.YOUTUBE_DEFAULT_DOWNLOAD, is_playlist=False)

    async def handle_youtube_link(self, event):
        try:
            self.logger.info(f"YouTube link detected in message ID: {event.message.id}")
            self.download_type = 'youtube'
            processing_message = await event.reply("Processing YouTube link...")

            match = re.search(r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+", event.message.text)
            if not match: 
                await processing_message.edit("Could not find a valid YouTube URL."); return

            url = match.group(0).rstrip(')')
            info, is_playlist, playlist_count = await asyncio.get_event_loop().run_in_executor(None, self.youtube_downloader.get_video_info, url)

            if info is None:
                await processing_message.edit("Could not process the YouTube URL."); return

            if is_playlist:
                buttons = [
                    [KeyboardButtonCallback("Download First", data=f"yt_playlist_first_{event.message.id}")],
                    [KeyboardButtonCallback(f"Download All ({playlist_count})", data=f"yt_playlist_all_{event.message.id}")]
                ]
                await processing_message.edit(f"This is a playlist with {playlist_count} videos. What would you like to do?", buttons=buttons)
            else:
                buttons = [
                    [KeyboardButtonCallback("Video", data=f"yt_single_video_{event.message.id}")],
                    [KeyboardButtonCallback("Audio", data=f"yt_single_audio_{event.message.id}")],
                    [KeyboardButtonCallback("Both", data=f"yt_single_both_{event.message.id}")]
                ]
                await processing_message.edit("What format would you like to download?", buttons=buttons)
            
            asyncio.create_task(self._start_timeout_task(processing_message, url))

        except Exception as e:
            self.logger.error(f"Error in handle_youtube_link: {e}")
            await event.reply(f"An error occurred: {e}")

    async def handle_youtube_choice(self, event):
        prompt_message = await event.get_message()
        if prompt_message.id in self.active_youtube_prompts:
            del self.active_youtube_prompts[prompt_message.id]
        else: # Timeout already handled or invalid prompt
            await event.answer("This action has expired."); return

        try:
            data = event.data.decode('utf-8')
            self.logger.info(f"YouTube choice callback received: {data}")

            parts = data.split('_')
            source_type, download_scope, original_message_id_str = parts[1], parts[2], parts[3]

            original_message = await self.bot.get_messages(event.chat_id, ids=int(original_message_id_str))
            if not original_message or not original_message.text:
                await event.edit("Could not find the original message."); return

            match = re.search(r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+", original_message.text)
            if not match: 
                await event.edit("Could not find a URL in the original message."); return
            url = match.group(0).rstrip(')')

            if source_type == 'playlist':
                is_playlist = (download_scope == 'all')
                buttons = [
                    [KeyboardButtonCallback("Video", data=f"yt_final_video_{is_playlist}_{original_message.id}")],
                    [KeyboardButtonCallback("Audio", data=f"yt_final_audio_{is_playlist}_{original_message.id}")],
                    [KeyboardButtonCallback("Both", data=f"yt_final_both_{is_playlist}_{original_message.id}")]
                ]
                await event.edit("What format would you like to download?", buttons=buttons)
                # We need a new timeout for this second prompt
                asyncio.create_task(self._start_timeout_task(prompt_message, url))
            
            elif source_type == 'final' or source_type == 'single':
                download_type = download_scope
                is_playlist = (parts[3] == 'True') if source_type == 'final' else False
                await event.edit(f"Selection received. Starting download...")
                await self._perform_youtube_download(event, url, download_type, is_playlist)

        except Exception as e:
            self.logger.error(f"Error in handle_youtube_choice: {e}")
            await event.answer(f"An error occurred: {e}")

    async def _perform_youtube_download(self, event, url, download_type, is_playlist):
        if isinstance(event, events.CallbackQuery.Event):
            message_to_edit = await event.get_message()
        else: # It's a Message object from a timeout
            message_to_edit = event

        main_loop = asyncio.get_event_loop()

        async def download_and_summarize(dl_type):
            start_time = time.time()
            last_update_time = 0

            def _progress_hook(d):
                nonlocal last_update_time
                if d['status'] == 'downloading':
                    current_time = time.time()
                    if current_time - last_update_time < 2: return
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    if not total_bytes: return
                    downloaded_bytes = d['downloaded_bytes']
                    percentage = (downloaded_bytes / total_bytes) * 100
                    speed = d.get('speed') or 0
                    eta = d.get('eta') or 0
                    video_title = d.get('info_dict', {}).get('title', 'Unknown')
                    progress_title = f"Downloading {dl_type.capitalize()}s" if is_playlist else f"Downloading {dl_type.capitalize()}"
                    progress_text = f"**{progress_title}:** {video_title}\n{percentage:.1f}% of {total_bytes/(1024*1024):.2f}MB at {speed/(1024*1024):.2f}MB/s, ETA: {eta:.0f}s"
                    asyncio.run_coroutine_threadsafe(message_to_edit.edit(progress_text, buttons=None), main_loop)
                    last_update_time = current_time

            info_dict, final_filename = await main_loop.run_in_executor(None, self.youtube_downloader.download, url, dl_type, _progress_hook, is_playlist)
            end_time = time.time()

            if not info_dict: return f"Could not download {dl_type}. Check logs."

            download_time = end_time - start_time
            if is_playlist:
                summary = DownloadSummary(message_to_edit, info_dict.get('title', 'N/A'), self.config_manager.get_youtube_download_path(dl_type), start_time, end_time, 0, None, None, None, status='completed', download_type='youtube')
                return summary.generate_summary()
            else:
                total_bytes = info_dict.get('filesize') or info_dict.get('filesize_approx') or 0
                summary = DownloadSummary(message_to_edit, os.path.basename(final_filename), os.path.dirname(final_filename), start_time, end_time, total_bytes, None, None, None, status='completed', download_type='youtube')
                return summary.generate_summary()

        try:
            if download_type == 'both':
                await message_to_edit.edit("Starting video download...", buttons=None)
                video_summary = await download_and_summarize('video')
                await message_to_edit.edit(video_summary + "\n\nStarting audio download...", buttons=None)
                audio_summary = await download_and_summarize('audio')
                await message_to_edit.edit(video_summary + "\n" + audio_summary, buttons=None)
            else:
                summary = await download_and_summarize(download_type)
                await message_to_edit.edit(summary, buttons=None)

        except Exception as e:
            self.logger.error(f"Error in _perform_youtube_download: {e}")
            await message_to_edit.edit(f"An error occurred: {e}")

    async def download_media(self, event):
        self.logger.info(f"download_media triggered for message ID: {event.message.id}")
        self.download_type = 'file'
        await self.process_download(event.message.id, event.chat_id)

    async def process_download(self, message_id, user_id, download_type=None):
        self.logger.info(f"process_download called for message ID: {message_id}")
        try:
            message = await self.bot.get_messages(user_id, ids=message_id)

            self.logger.info(f"message:::: {message}")

            file_extension = self.telethon_utils.get_file_extension(message)
            origin_group = self.telethon_utils.get_origin_group(message)
            channel_id = self.telethon_utils.get_channel_id(message)
            file_info = self.telethon_utils.get_file_info(message, origin_group)

            self.logger.info(f"download_media file_info: [{message.id}] {file_info} sender_id: {message.sender_id} origin_group: {origin_group} channel_id: {channel_id}")
            self.logger.info(f"download_media download_type: [{download_type}]")
            self.logger.info(f"download_media self.download_type: [{self.download_type}]")

            if download_type:
                self.download_type = download_type
            
            self.logger.info(f"download_media self.download_type: [{self.download_type}]")

            target_download_dir, final_destination_dir = self.download_manager.get_download_dirs(file_extension, origin_group, channel_id, file_info)

            initial_message = await message.reply(f"Added to queued {file_info}...")
            start_time = time.time()

            self.download_cancellation_flags[initial_message.id] = asyncio.Event()
            self.logger.info(f"Populating download_cancellation_flags with message ID: {initial_message.id}")

            file_size = self.telethon_utils.get_file_size(message)

            original_filename = os.path.join(target_download_dir, file_info)
            download_path_with_filename = None # Initialize here

            self.download_tracker.add_download(initial_message.id, message.id, original_filename, message.media, origin_group, user_id, file_info, download_type=download_type if download_type else self.download_type, current_file_path=download_path_with_filename)

            download_summary_downloading = DownloadSummary(message, file_info, final_destination_dir, start_time, 0, file_size, origin_group, user_id, channel_id, status='downloading')

            progress_bar = None

            if channel_id:
                log_message_chat_id = f"Channel ID: {channel_id}"
            else:
                log_message_chat_id = f"User ID: {origin_group}"
            self.logger.info(f"Added to queued {file_info} from {log_message_chat_id}")

            async with self.download_semaphore:
                start_time = time.time()
                await initial_message.edit(f"Starting download of {file_info} from {log_message_chat_id}")

                self.logger.info(f"Starting download of {file_info} user_id {user_id} from {log_message_chat_id}")
                try:
                    media_to_download = None
                    if message.document:
                        media_to_download = message.document
                    elif message.photo:
                        media_to_download = message.photo

                    if media_to_download:
                        download_path_with_filename = os.path.join(target_download_dir, file_info)
                        if self.env_config.PROGRESS_DOWNLOAD.lower() == 'true':
                            progress_bar = ProgressBar(initial_message, file_info, self.logger, final_destination_dir, file_size, start_time, origin_group, user_id, int(self.env_config.PROGRESS_STATUS_SHOW), channel_id, self.download_cancellation_flags.get(initial_message.id))
                            download_task = asyncio.create_task(self.bot.download_media(media_to_download, file=download_path_with_filename, progress_callback=progress_bar.progress_callback))
                        else:
                            download_task = asyncio.create_task(self.bot.download_media(media_to_download, file=download_path_with_filename))
                        self.active_downloads[initial_message.id] = download_task
                        downloaded_file_path = await download_task
                    else:
                        self.logger.error(f"No downloadable media found in message {message.id}")
                        await initial_message.edit(f"Error: No downloadable media found in message.")
                        return
                    end_time = time.time()

                    if file_extension.lower() == 'torrent':
                        self.downloaded_files[initial_message.id] = {
                            'original_message_id': message.id,
                            'downloaded_file_path': downloaded_file_path,
                            'final_destination_dir': final_destination_dir,
                            'file_info': file_info,
                            'file_extension': file_extension,
                            'file_size': file_size,
                            'origin_group': origin_group,
                            'user_id': user_id,
                            'channel_id': channel_id,
                            'start_time': start_time,
                            'end_time': end_time,
                            'initial_message_id': initial_message.id,
                            'initial_message_chat_id': initial_message.chat_id
                        }
                        await self._ask_for_torrent_source_category(initial_message, 'file', downloaded_file_path)
                        return # Exit here, processing continues after category selection
                    else:
                        final_file_path = self.download_manager.move_to_completed(downloaded_file_path, final_destination_dir)
                        if final_file_path:
                            await self._finalize_download_processing(initial_message, message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, user_id, channel_id, file_extension, final_file_path)
                        else:
                            self.logger.error(f"Failed to move file {file_info} to completed directory.")
                            await initial_message.edit(f"Error: Failed to move file {file_info} to completed directory.")
                except asyncio.CancelledError:
                    self.logger.info(f"Caught asyncio.CancelledError for download of {file_info} (message ID: {initial_message.id}).")
                    self.download_tracker.update_status(message.id, 'cancelled', final_filename=None, download_type=self.download_type)
                    self.download_tracker.remove_download(message.id, download_type=self.download_type)
                    if os.path.exists(download_path_with_filename):
                        os.remove(download_path_with_filename)
                        self.logger.info(f"Deleted partially downloaded file: {download_path_with_filename}")
                    await initial_message.edit(f"Download of {file_info} cancelled.", buttons=None)
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
            action_parts = data.split('_')
            action = '_'.join(action_parts[:2]) if action_parts[0] == 'resume' or (action_parts[0] == 'cancel' and action_parts[1] == 'download') else action_parts[0]
            if action_parts[0] == 'category':
                action = action_parts[0]            
            
            if action == 'category':
                message_id = int(parts[1])
                category = unquote(parts[2]) if len(parts) > 2 else None

                if message_id not in self.downloaded_files:
                    await event.answer("Original download information not found.")
                    return

                download_info = self.downloaded_files[message_id]
                source_type = download_info.get('source_type', 'file') # Default to 'file' for existing torrents

                if source_type == 'file':
                    torrent_path = download_info['downloaded_file_path']
                    destination_path = download_info['final_destination_dir']
                elif source_type == 'magnet':
                    magnet_uri = download_info['source_data']
                    # For magnet links, destination_path is not directly used here for adding, but might be needed for _finalize_download_processing
                    destination_path = None # Or retrieve from download_info if stored for magnets

                if category == 'new':
                    self.downloaded_files[message_id]['waiting_for_category_name'] = True
                    await self.bot.edit_message(event.chat_id, message_id, "Please send the name for the new category.", buttons=None)
                else:
                    final_file_path = None
                    if source_type == 'file':
                        final_file_path = self.download_manager.move_to_completed(torrent_path, destination_path, category=category if category != 'none' else None)
                    elif source_type == 'magnet':
                        final_file_path = self.download_manager.add_magnet_link_with_category(magnet_uri, category if category != 'none' else None)

                    if final_file_path:
                        initial_message = await self.bot.get_messages(download_info['initial_message_chat_id'], ids=download_info['initial_message_id'])
                        original_message = await self.bot.get_messages(download_info['user_id'], ids=download_info['original_message_id'])
                        file_info = download_info['file_info']
                        file_extension = download_info['file_extension'] if source_type == 'file' else 'torrent' # Assume torrent for magnet
                        file_size = download_info['file_size'] if source_type == 'file' else 0 # No file size for magnet initially
                        origin_group = download_info['origin_group'] if source_type == 'file' else None
                        user_id = download_info['user_id']
                        channel_id = download_info['channel_id'] if source_type == 'file' else None
                        start_time = download_info['start_time'] if source_type == 'file' else time.time()
                        end_time = time.time()

                        await self.bot.edit_message(initial_message.chat_id, initial_message.id, "Processing torrent...", buttons=None)
                        await self._finalize_download_processing(initial_message, original_message, file_info, destination_path, start_time, end_time, file_size, origin_group, user_id, channel_id, file_extension, final_file_path)
                    else:
                        await self.bot.edit_message(event.chat_id, message_id, "Failed to add torrent.", buttons=None)
                    del self.downloaded_files[message_id]
                return

            if data.startswith('cancel_download'):
                message_id = int(parts[2])
                self.logger.info(f"Cancelling download for message ID: {message_id}")
                await event.edit("Download cancelled.", buttons=None)
                if message_id in self.download_cancellation_flags:
                    self.download_cancellation_flags[message_id].set()
                    self.logger.info(f"Cancellation flag set for message ID: {message_id}")
                if message_id in self.active_downloads:
                    self.active_downloads[message_id].cancel()
                    self.logger.info(f"Download task cancelled for message ID: {message_id}")
                    del self.active_downloads[message_id]
                    del self.download_cancellation_flags[message_id]
                else:
                    await event.answer("Could not find download to cancel.")
                return

            self.logger.info(f"Action: {action}")

            if action.startswith('resume'):
                if action == 'resume_one':
                    message_id = int(action_parts[2])
                    await self.pending_downloads_manager.resume_one(message_id, event)
                elif action == 'resume_all':
                    await self.pending_downloads_manager.resume_all(event)
                elif action == 'resume_cancel':
                    await self.pending_downloads_manager.cancel(event)
                return

            message_id = int(parts[1])

            if action == 'move':
                if message_id in self.downloaded_files:
                    file_info = self.downloaded_files[message_id]
                    self.downloaded_files[message_id]['browser_chat_id'] = event.chat_id
                    self.downloaded_files[message_id]['browser_message_id'] = event.message_id
                    if self.keyboard_manager:
                        summary_text = file_info.get('summary_text', "")
                        text, buttons = await self.keyboard_manager.send_directory_browser(message_id, file_info['current_dir'], summary_text=summary_text)
                        await event.edit(text, buttons=buttons)
                    else:
                        await event.answer("Keyboard manager not initialized.")
            elif action == 'ok' or action == 'cancel':
                if message_id in self.downloaded_files:
                    summary_text = self.downloaded_files[message_id].get('summary_text', "Download operation ok.")
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
                    self.downloaded_files[message_id]['current_dir'] = new_full_path
                    if self.keyboard_manager:
                        text, buttons = await self.keyboard_manager.send_directory_browser(message_id, new_full_path, page=0)
                        await event.edit(text, buttons=buttons)
                    else:
                        await event.answer("Keyboard manager not initialized.")
            elif action == 'nav':
                nav_action = parts[2]
                current_dir_from_state = self.downloaded_files[message_id]['current_dir']
                page = int(parts[4])

                if message_id in self.downloaded_files:
                    if nav_action == 'next':
                        page += 1
                        self.downloaded_files[message_id]['current_dir'] = current_dir_from_state
                    elif nav_action == 'back':
                        page -= 1
                        self.downloaded_files[message_id]['current_dir'] = current_dir_from_state
                    elif nav_action == 'up':
                        new_current_dir = os.path.dirname(current_dir_from_state)
                        self.downloaded_files[message_id]['current_dir'] = new_current_dir
                        page = 0
                    elif nav_action == 'this':
                        file_info = self.downloaded_files[message_id]
                        file_path = file_info['file_path']
                        destination_dir = current_dir_from_state
                        summary_text = file_info.get('summary_text', "")
                        new_file_path = self.download_manager.move_file(file_path, destination_dir)
                        if new_file_path:
                            self.download_tracker.update_status(message_id, 'completed', final_filename=new_file_path, download_type=self.download_type)
                            await event.edit(f"{summary_text}\n\nFile moved successfully to {new_file_path}", buttons=None)
                            del self.downloaded_files[message_id]
                        else:
                            await event.edit(f"{summary_text}\n\nError moving file.", buttons=None)
                        return
                    
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
            target_message_id = None
            for msg_id, file_info in self.downloaded_files.items():
                if file_info.get('waiting_for_folder_name', False):
                    target_message_id = msg_id
                    break

            if target_message_id is None:
                return

            new_folder_name = event.message.text
            current_dir = self.downloaded_files[target_message_id]['current_dir']
            new_folder_path = os.path.join(current_dir, new_folder_name)
            browser_message_id = self.downloaded_files[target_message_id].get('browser_message_id', None)
            browser_chat_id = self.downloaded_files[target_message_id].get('browser_chat_id', None)

            os.makedirs(new_folder_path, exist_ok=True)
            self.download_manager._apply_permissions_and_ownership(new_folder_path)
            self.downloaded_files[target_message_id]['waiting_for_folder_name'] = False

            file_info = self.downloaded_files[target_message_id]
            file_path = file_info['file_path']
            new_file_path = self.download_manager.move_file(file_path, new_folder_path)

            if new_file_path:
                self.download_tracker.update_status(target_message_id, 'completed', final_filename=new_file_path, download_type=self.download_type)
                summary_text = self.downloaded_files[target_message_id].get('summary_text', "")
                await self.bot.edit_message(browser_chat_id, browser_message_id, f"{summary_text}\n\nFolder '{new_folder_name}' created and file moved successfully to {new_file_path}", buttons=None)
                del self.downloaded_files[target_message_id]
            else:
                await event.reply(f"Folder '{new_folder_name}' created, but there was an error moving the file.")

            if browser_message_id and browser_chat_id:
                self.logger.info(f"Refreshing browser for message {target_message_id}")
        except Exception as e:
            self.logger.error(f"Error creating new folder: {e}")
            await event.reply(f"Error creating folder: {e}")

    async def handle_text_commands(self, event):
        message_text = event.message.text
        sender_id = event.sender_id

        if message_text.startswith('/'):
            command_name = message_text.split(' ')[0]
            await self.commands_manager.execute_command(command_name, event)
        elif sender_id in self.commands_manager.active_rename_prompts:
            # This is a response to a rename prompt
            await self.commands_manager.handle_new_rename_input(event)

    async def handle_magnet_link(self, event):
        self.logger.info(f"Magnet link detected in message ID: {event.message.id}")
        self.download_type = 'magnet'
        magnet_uri = event.message.text
        initial_message = await event.reply(f"Magnet link received. Choosing category...")

        self.downloaded_files[initial_message.id] = {
            'original_message_id': event.message.id,
            'source_type': 'magnet',
            'source_data': magnet_uri,
            'file_info': magnet_uri, # Using magnet URI as file_info for now
            'user_id': event.sender_id,
            'initial_message_id': initial_message.id,
            'initial_message_chat_id': initial_message.chat_id
        }
        await self._ask_for_torrent_source_category(initial_message, 'magnet', magnet_uri)

    async def handle_direct_link(self, event):
        try:
            self.logger.info(f"Direct link detected in message ID: {event.message.id}")
            self.download_type = 'link'
            url = event.message.text.strip()
            initial_message = await event.reply(f"Processing direct link: {url}")
            await self.direct_downloader.download_file(event, url, initial_message)
        except Exception as e:
            self.logger.error(f"Error in handle_direct_link: {e}")
            await event.reply(f"An error occurred: {e}")

    async def handle_new_category_name(self, event):
        try:
            target_message_id = None
            for msg_id, file_info in self.downloaded_files.items():
                if file_info.get('waiting_for_category_name', False):
                    target_message_id = msg_id
                    break

            if target_message_id is None:
                return

            new_category_name = event.message.text
            download_info = self.downloaded_files[target_message_id]
            source_type = download_info.get('source_type', 'file')
            source_data = download_info.get('downloaded_file_path') or download_info.get('source_data')
            destination_path = download_info.get('final_destination_dir') if source_type == 'file' else None
            browser_message_id = download_info.get('browser_message_id', None)
            browser_chat_id = download_info.get('browser_chat_id', None)

            final_file_path = None
            if source_type == 'file':
                final_file_path = self.download_manager.move_to_completed(source_data, destination_path, category=new_category_name)
            elif source_type == 'magnet':
                final_file_path = self.download_manager.add_magnet_link_with_category(source_data, new_category_name)

            if final_file_path:
                # Retrieve original message details for _finalize_download_processing
                original_message_id = download_info['original_message_id']
                original_message = await self.bot.get_messages(download_info['user_id'], ids=original_message_id)
                file_info = download_info['file_info']
                file_extension = download_info['file_extension'] if source_type == 'file' else 'torrent'
                file_size = download_info['file_size'] if source_type == 'file' else 0
                origin_group = download_info['origin_group'] if source_type == 'file' else None
                user_id = download_info['user_id']
                channel_id = download_info['channel_id'] if source_type == 'file' else None
                start_time = download_info['start_time'] if source_type == 'file' else time.time()
                end_time = time.time()
                initial_message = await self.bot.get_messages(download_info['initial_message_chat_id'], ids=download_info['initial_message_id'])

                await self.bot.edit_message(initial_message.chat_id, initial_message.id, "Processing torrent...", buttons=None)
                await self._finalize_download_processing(initial_message, original_message, file_info, destination_path, start_time, end_time, file_size, origin_group, user_id, channel_id, file_extension, final_file_path)
                await event.delete()
            else:
                await self.bot.edit_message(browser_chat_id, browser_message_id, "Failed to add torrent.", buttons=None)

            del self.downloaded_files[target_message_id]
        except Exception as e:
            self.logger.error(f"Error handling new category name: {e}")
            await event.reply(f"Error creating new category: {e}")

    

    async def _finalize_download_processing(self, initial_message, message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, user_id, channel_id, file_extension, final_file_path):
        self.logger.info(f"Finished download of [{message.id}] [{file_info}] to [{final_file_path}]")
        
        await asyncio.sleep(0.5)

        self.download_tracker.update_status(message.id, 'completed', final_filename=final_file_path, download_type=self.download_type)

        summary = DownloadSummary(message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, user_id, channel_id, status='completed', download_type=self.download_type)
        summary_text = summary.generate_summary()

        self.downloaded_files[message.id] = {
            'file_path': final_file_path,
            'current_dir': self.env_config.BASE_DOWNLOAD_PATH,
            'summary_text': summary_text
        }

        buttons = None
        if file_extension.lower() != 'torrent':
            buttons = summary.get_buttons(self.keyboard_manager)

        try:
            await initial_message.edit(summary_text, buttons=buttons.rows if buttons else None)
        except Exception as edit_error:
            self.logger.error(f"Error editing message with buttons for {file_info}: {edit_error}")
            await initial_message.edit(f"Download completed, but error displaying buttons: {edit_error}")

    async def _ask_for_torrent_source_category(self, initial_message, source_type, source_data):
        categories = self.download_manager.torrent_manager.get_categories()
        buttons = []
        for category in categories:
            buttons.append([KeyboardButtonCallback(category, data=f"category_{initial_message.id}_{quote(category)}")])
        buttons.append([KeyboardButtonCallback("Add New Category", data=f"category_{initial_message.id}_new")])
        buttons.append([KeyboardButtonCallback("No Category", data=f"category_{initial_message.id}_none")])
        await self.bot.edit_message(initial_message.chat_id, initial_message.id, "Choose a category for the torrent:", buttons=buttons)

    async def run(self):
        try:
            await self.bot.start(bot_token=self.BOT_TOKEN)
            self.welcome_message_generator.log_welcome_message()
            try:
                await self.bot.send_message(self.AUTHORIZED_USER_IDS[0], self.welcome_message_generator.get_message())
                pending_downloads = self.download_tracker.get_pending_downloads()
                await self.resume_manager.ask_to_resume(pending_downloads, self.AUTHORIZED_USER_IDS[0])
            except Exception as e:
                self.logger.error(f"Error sending start message to authorized user: {e}")
            await self.bot.run_until_disconnected()
        except Exception as e:
            self.logger.error(f"Unhandled exception in run: {e}")

if __name__ == "__main__":
    bot_instance = TelethonDownloaderBot()
    asyncio.run(bot_instance.run())