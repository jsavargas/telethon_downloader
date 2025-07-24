import time

class DownloadSummary:
    def __init__(self, message, file_info, download_dir, start_time, end_time, file_size, origin_group):
        self.message = message
        self.file_info = file_info
        self.download_dir = download_dir
        self.start_time = start_time
        self.end_time = end_time
        self.file_size = file_size
        self.origin_group = origin_group

    def generate_summary(self):
        download_time = self.end_time - self.start_time

        download_speed = (self.file_size / download_time) if download_time > 0 else 0

        summary_text = (
            f"Download completed\n\n"
            f"File Name: {self.file_info}\n"
            f"Download Folder: {self.download_dir}\n"
            f"File Size: {self.file_size / (1024*1024):.2f} MB\n"
            f"Start Time: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}\n"
            f"End Time: {time.strftime('%H:%M:%S', time.localtime(self.end_time))}\n"
            f"Download Time: {download_time:.2f} seconds\n"
            f"Download Speed: {download_speed / 1024:.2f} KB/s\n"
            f"Origin Group: {self.origin_group}"
        )
        return summary_text