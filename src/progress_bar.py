import time

class ProgressBar:
    def __init__(self, initial_message, file_info, logger, download_dir, file_size, start_time, origin_group, progress_status_show):
        self.initial_message = initial_message
        self.file_info = file_info
        self.logger = logger
        self.download_dir = download_dir
        self.total_file_size = file_size
        self.start_time = start_time
        self.origin_group = origin_group
        self.progress_status_show = progress_status_show
        self.last_percentage_sent = -1

    async def progress_callback(self, current, total):
        percentage = (current / total) * 100
        elapsed_time = time.time() - self.start_time
        
        if percentage - self.last_percentage_sent >= self.progress_status_show or percentage == 100:
            self.last_percentage_sent = percentage

            if elapsed_time > 0:
                speed = current / elapsed_time
                eta = (total - current) / speed if speed > 0 else 0
            else:
                speed = 0
                eta = 0

            progress_text = (
                f"Downloading {self.file_info}\n\n"
                f"File Name: {self.file_info}\n"
                f"Download Folder: {self.download_dir}\n"
                f"File Size: {self.total_file_size / (1024*1024):.2f} MB\n"
                f"Start Time: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}\n"
                f"Progress: {current / (1024*1024):.2f}MB / {total / (1024*1024):.2f}MB ({percentage:.2f}%)\n"
                f"Speed: {speed / (1024*1024):.2f}MB/s\n"
                f"ETA: {eta:.0f}s\n"
                f"Origin Group: {self.origin_group}"
            )
            
            try:
                await self.initial_message.edit(progress_text)
            except Exception as e:
                self.logger.error(f"Error updating progress message: {e}")