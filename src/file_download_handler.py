import os
import time
import asyncio
from progress_bar import ProgressBar
from download_summary import DownloadSummary


class FileDownloadHandler:
    def __init__(self, bot, download_manager, download_tracker, telethon_utils, env_config, keyboard_manager, download_semaphore, downloaded_files, media_groups, logger):
        self.bot = bot
        self.download_manager = download_manager
        self.download_tracker = download_tracker
        self.telethon_utils = telethon_utils
        self.env_config = env_config
        self.keyboard_manager = keyboard_manager
        self.download_semaphore = download_semaphore
        self.downloaded_files = downloaded_files
        self.media_groups = media_groups
        self.logger = logger
        self.download_cancellation_flags = {}
        self.active_downloads = {}
        # Wired by TelethonDownloaderBot after both are constructed — each needs the other.
        self.torrent_magnet_handler = None
        self.file_browser_handler = None

    async def download_media(self, event):
        self.logger.info(f"download_media triggered for message ID: {event.message.id}")
        await self.process_download(event.message.id, event.chat_id, download_type='file')

    async def process_download(self, message_id, user_id, download_type='file'):
        self.logger.info(f"process_download called for message ID: {message_id}")
        try:
            message = await self.bot.get_messages(user_id, ids=message_id)
            self.logger.info(f"message:::: {message}")

            file_extension = self.telethon_utils.get_file_extension(message)
            origin_group = self.telethon_utils.get_origin_group(message)
            channel_id = self.telethon_utils.get_channel_id(message)
            file_info = self.telethon_utils.get_file_info(message, origin_group)

            self.logger.info(f"download_media file_info: [{message.id}] {file_info} origin_group: {origin_group} channel_id: {channel_id}")
            self.logger.info(f"download_media file_extension: [{file_extension}]")
            self.logger.info(f"download_media download_type: [{download_type}]")

            _file_extension = os.path.splitext(file_info)[1].lstrip('.')
            if not _file_extension:
                file_info = f"{file_info}.{file_extension}"

            target_download_dir, final_destination_dir = self.download_manager.get_download_dirs(file_extension, origin_group, channel_id, file_info)

            initial_message = await message.reply(f"Added to queued {file_info}...")
            start_time = time.time()

            group_key = int(message.date.timestamp())
            if group_key not in self.media_groups:
                self.media_groups[group_key] = {
                    'total_files': 0,
                    'completed_files': 0,
                    'files': {},
                    'initial_message_id': None,
                    'user_facing_group_id': group_key
                }
            self.media_groups[group_key]['total_files'] += 1
            self.media_groups[group_key]['files'][message.id] = {
                'status': 'downloading', 'path': None,
                'initial_message_id': initial_message.id, 'filename': file_info
            }
            if not self.media_groups[group_key]['initial_message_id']:
                self.media_groups[group_key]['initial_message_id'] = initial_message.id

            self.download_cancellation_flags[initial_message.id] = asyncio.Event()

            file_size = self.telethon_utils.get_file_size(message)
            original_filename = os.path.join(target_download_dir, file_info)
            download_path_with_filename = None

            self.download_tracker.add_download(
                initial_message.id, message.id, original_filename, message.media,
                origin_group, user_id, file_info, download_type=download_type,
                current_file_path=download_path_with_filename,
                download_date=int(message.date.timestamp())
            )

            if channel_id:
                log_message_chat_id = f"Channel ID: {channel_id}"
            else:
                log_message_chat_id = f"User ID: {origin_group}"
            self.logger.info(f"Added to queued {file_info} from {log_message_chat_id}")

            async with self.download_semaphore:
                start_time = time.time()
                await initial_message.edit(f"Starting download of {file_info} from {log_message_chat_id}")
                try:
                    media_to_download = message.document or message.photo
                    if media_to_download:
                        download_path_with_filename = os.path.join(target_download_dir, file_info)
                        if self.env_config.PROGRESS_DOWNLOAD.lower() == 'true':
                            progress_bar = ProgressBar(
                                initial_message, file_info, self.logger, final_destination_dir,
                                file_size, start_time, origin_group, user_id,
                                int(self.env_config.PROGRESS_STATUS_SHOW), channel_id,
                                self.download_cancellation_flags.get(initial_message.id)
                            )
                            download_task = asyncio.create_task(
                                self.bot.download_media(media_to_download, file=download_path_with_filename, progress_callback=progress_bar.progress_callback)
                            )
                        else:
                            download_task = asyncio.create_task(
                                self.bot.download_media(media_to_download, file=download_path_with_filename)
                            )
                        self.active_downloads[initial_message.id] = download_task
                        downloaded_file_path = await download_task
                    else:
                        self.logger.error(f"No downloadable media found in message {message.id}")
                        await initial_message.edit("Error: No downloadable media found in message.")
                        return

                    end_time = time.time()

                    if self.env_config.TORRENT_MODE.lower() != 'watch' and file_extension.lower() == 'torrent':
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
                            'initial_message_chat_id': initial_message.chat_id,
                            'download_type': download_type,
                        }
                        await self.torrent_magnet_handler.ask_for_category(initial_message)
                        return
                    else:
                        final_file_path = self.download_manager.move_to_completed(downloaded_file_path, final_destination_dir)
                        if final_file_path:
                            await self._finalize_download_processing(initial_message, message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, user_id, channel_id, file_extension, final_file_path, download_type=download_type)
                        else:
                            self.logger.error(f"Failed to move file {file_info} to completed directory.")
                            await initial_message.edit(f"Error: Failed to move file {file_info} to completed directory.")

                except asyncio.CancelledError:
                    self.logger.info(f"Download cancelled: {file_info} (message ID: {initial_message.id})")
                    self.download_tracker.update_status(message.id, 'cancelled', final_filename=None, download_type=download_type)
                    self.download_tracker.remove_download(message.id, download_type=download_type)
                    if download_path_with_filename and os.path.exists(download_path_with_filename):
                        os.remove(download_path_with_filename)
                    await initial_message.edit(f"Download of {file_info} cancelled.", buttons=None)
                except Exception as e:
                    self.logger.error(f"Error downloading {file_info}: {e}")
                    await initial_message.edit(f"Error downloading {file_info}: {e}")
        except Exception as e:
            self.logger.error(f"Unhandled exception in process_download: {e}")

    def cancel_download(self, message_id):
        if message_id in self.download_cancellation_flags:
            self.download_cancellation_flags[message_id].set()
        if message_id in self.active_downloads:
            self.active_downloads[message_id].cancel()
            del self.active_downloads[message_id]
            del self.download_cancellation_flags[message_id]
            return True
        return False

    async def _finalize_download_processing(self, initial_message, message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, user_id, channel_id, file_extension, final_file_path, download_type='file'):
        self.logger.info(f"Finished download of [{message.id}] [{file_info}] to [{final_file_path}]")

        await asyncio.sleep(0.5)

        self.download_tracker.update_status(message.id, 'completed', final_filename=final_file_path, download_type=download_type)

        file_info = os.path.basename(final_file_path)

        summary = DownloadSummary(message, file_info, final_destination_dir, start_time, end_time, file_size, origin_group, user_id, channel_id, status='completed', download_type=download_type)
        summary_text = summary.generate_summary()

        self.downloaded_files[message.id] = {
            'file_path': final_file_path,
            'current_dir': self.env_config.BASE_DOWNLOAD_PATH,
            'summary_text': summary_text,
            'download_type': download_type,
        }

        buttons = None
        if file_extension.lower() != 'torrent':
            buttons = summary.get_buttons(self.keyboard_manager)

        try:
            await initial_message.edit(summary_text, buttons=buttons.rows if buttons else None)
        except Exception as edit_error:
            self.logger.error(f"Error editing message with buttons for {file_info}: {edit_error}")
            await initial_message.edit(f"Download completed, but error displaying buttons: {edit_error}")

        group_key = int(message.date.timestamp())
        if group_key in self.media_groups:
            group_info = self.media_groups[group_key]
            group_info['completed_files'] += 1
            group_info['files'][message.id]['status'] = 'completed'
            group_info['files'][message.id]['path'] = final_file_path

            if group_info['completed_files'] == group_info['total_files']:
                await self.file_browser_handler.handle_media_group_completion(group_key, message.chat_id)
