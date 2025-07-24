import os

class DownloadManager:
    def __init__(self, base_download_path):
        self.base_download_path = base_download_path
        self.incompleted_dir = os.path.join(self.base_download_path, "incompleted")
        self.completed_dir = os.path.join(self.base_download_path, "completed")
        os.makedirs(self.incompleted_dir, exist_ok=True)
        os.makedirs(self.completed_dir, exist_ok=True)

    def get_incompleted_dir(self):
        return self.incompleted_dir

    def get_completed_dir(self):
        return self.completed_dir

    def move_to_completed(self, downloaded_file_path):
        final_file_path = os.path.join(self.completed_dir, os.path.basename(downloaded_file_path))
        os.rename(downloaded_file_path, final_file_path)
        return final_file_path
