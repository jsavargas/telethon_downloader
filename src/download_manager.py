import os

class DownloadManager:
    def __init__(self, base_download_path, config_manager):
        self.base_download_path = base_download_path
        self.config_manager = config_manager

        # Default incompleted and completed directories
        self.default_incompleted_dir = os.path.join(self.base_download_path, "incompleted")
        self.default_completed_dir = os.path.join(self.base_download_path, "completed")
        os.makedirs(self.default_incompleted_dir, exist_ok=True)
        os.makedirs(self.default_completed_dir, exist_ok=True)

        # Temporary directory for in-progress downloads when a specific final path is given
        self.temp_incompleted_dir = os.path.join(self.base_download_path, "temp_incompleted")
        os.makedirs(self.temp_incompleted_dir, exist_ok=True)

    def get_download_dirs(self, extension):
        configured_path = self.config_manager.get_download_path(extension)
        if configured_path:
            # If a specific path is configured, use it as the final destination
            # and use a temporary incompleted directory
            target_incompleted_dir = self.temp_incompleted_dir
            target_completed_dir = configured_path
            os.makedirs(target_completed_dir, exist_ok=True)
            return target_incompleted_dir, target_completed_dir
        else:
            # Otherwise, use the default incompleted/completed structure
            return self.default_incompleted_dir, self.default_completed_dir

    def move_to_completed(self, downloaded_file_path, target_completed_dir):
        final_file_path = os.path.join(target_completed_dir, os.path.basename(downloaded_file_path))
        os.rename(downloaded_file_path, final_file_path)
        return final_file_path