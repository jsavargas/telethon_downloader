import time
import logging

class DownloadSummary:
    def __init__(self, message, file_info, download_dir, start_time, end_time, file_size, origin_group, user_id=None, channel_id=None, status='downloading'):
        self.message = message
        self.file_info = file_info
        self.download_dir = download_dir
        self.start_time = start_time
        self.end_time = end_time
        self.file_size = file_size
        self.origin_group = origin_group
        self.user_id = user_id
        self.channel_id = channel_id
        self.logger = logging.getLogger(__name__)
        self.status = status

    def generate_summary(self):
        try:
            download_time = self.end_time - self.start_time

            download_speed = (self.file_size / download_time) if download_time > 0 else 0

            summary_text = (
                f"Download completed\n\n"
                f"**File Name:** {self.file_info}\n"
                f"**Download Folder:** {self.download_dir}\n"
                f"**File Size:** {self.file_size / (1024*1024):.2f} MB\n"
                f"**Start Time:** {time.strftime('%H:%M:%S', time.localtime(self.start_time))}\n"
                f"**End Time:** {time.strftime('%H:%M:%S', time.localtime(self.end_time))}\n"
                f"**Download Time:** {download_time:.2f} seconds\n"
                f"**Download Speed:** {download_speed / 1024:.2f} KB/s\n"
                f"**User Id:** {self.user_id}\n"
                f"**Origin Group:** {self.origin_group}"
            )

            if self.channel_id:
                summary_text += f"\nChannel ID: {self.channel_id}"

            return summary_text
        except Exception as e:
            self.logger.error(f"Error generating download summary: {e}")
            return "Error generating download summary."

    def get_buttons(self, keyboard_manager):
        try:
            return keyboard_manager.get_download_buttons(self.message.id)
        except Exception as e:
            self.logger.error(f"Error getting buttons for download summary: {e}")
            return None

    def to_dict(self):
        return {
            'message_id': self.message.id,
            'file_info': self.file_info,
            'download_dir': self.download_dir,
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)),
            'end_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time)),
            'file_size': self.file_size,
            'origin_group': self.origin_group,
            'channel_id': self.channel_id,
            'summary_text': self.generate_summary(),
            'status': self.status,
            'download_date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))
        }