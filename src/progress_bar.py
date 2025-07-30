import time
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup

class ProgressBar:
    def __init__(self, initial_message, file_info, logger, download_dir, file_size, start_time, origin_group, user_id, progress_status_show, channel_id=None, cancellation_flag=None):
        self.initial_message = initial_message
        self.file_info = file_info
        self.logger = logger
        self.download_dir = download_dir
        self.total_file_size = file_size
        self.start_time = start_time
        self.origin_group = origin_group
        self.user_id = user_id
        self.progress_status_show = progress_status_show
        self.channel_id = channel_id
        self.last_percentage_sent = -1
        self.cancellation_flag = cancellation_flag

    async def progress_callback(self, current, total):
        try:
            if self.cancellation_flag and self.cancellation_flag.is_set():
                self.logger.info(f"Cancellation flag detected for {self.file_info}. Raising CancelledError.")
                raise asyncio.CancelledError("Download cancelled by user.")

            percentage = (current / total) * 100
            elapsed_time = time.time() - self.start_time

            if percentage - self.last_percentage_sent >= self.progress_status_show or percentage == 100 or self.last_percentage_sent == -1:
                self.last_percentage_sent = percentage

                self.logger.info(f"progress_callback percentage: {self.file_info} {percentage}")
                if elapsed_time > 0:
                    speed = current / elapsed_time
                    eta = (total - current) / speed if speed > 0 else 0
                else:
                    speed = 0
                    eta = 0

                progress_text = (
                    f"Downloading \n\n"
                    f"**File Name:** {self.file_info}\n"
                    f"**Download Folder:** {self.download_dir}\n"
                    f"**File Size:** {self.total_file_size / (1024*1024):.2f} MB\n"
                    f"**Start Time:** {time.strftime('%H:%M:%S', time.localtime(self.start_time))}\n"
                    f"**Progress:** {current / (1024*1024):.2f}MB / {total / (1024*1024):.2f}MB ({percentage:.2f}%)\n"
                    f"**Speed:** {speed / (1024*1024):.2f}MB/s\n"
                    f"**ETA:** {eta:.0f}s\n"
                    f"**User Id:** {self.user_id}\n"
                    f"**Origin Group:** {self.origin_group}"
                )

                if self.channel_id:
                    progress_text += f"\nChannel ID: {self.channel_id}"
                
                buttons = ReplyInlineMarkup([[
                    KeyboardButtonCallback("Cancel Download", data=f"cancel_download_{self.initial_message.id}".encode('utf-8'))
                ]])

                try:
                    await self.initial_message.edit(progress_text, buttons=buttons.rows)
                except Exception as e:
                    self.logger.error(f"Error updating progress message: {e}")
        except asyncio.CancelledError:
            self.logger.info(f"Download of {self.file_info} cancelled by user.")
            raise # Re-raise to stop the download
        except Exception as e:
            self.logger.error(f"Unhandled exception in progress_callback: {e}")