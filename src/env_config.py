import os

class EnvConfig:
    def __init__(self):
        self.API_ID = os.environ.get("API_ID") or os.environ.get("TG_API_ID")
        self.API_HASH = os.environ.get("API_HASH") or os.environ.get("TG_API_HASH")
        self.BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TG_BOT_TOKEN")
        self.AUTHORIZED_USER_ID = os.environ.get("AUTHORIZED_USER_ID") or os.environ.get("TG_AUTHORIZED_USER_ID")
        self.BASE_DOWNLOAD_PATH = os.environ.get("TG_DOWNLOAD_PATH") or os.environ.get("DOWNLOAD_PATH", '/download')
        self.PATH_CONFIG = os.environ.get("PATH_CONFIG", '/config/config.ini')
        self.PUID = os.environ.get('PUID')
        self.PGID = os.environ.get('PGID')
        self.YTDLP_VERSION = os.environ.get('YTDLP_VERSION', 'N/A')
        self.PROGRESS_DOWNLOAD = os.environ.get('PROGRESS_DOWNLOAD', 'True')
        self.PROGRESS_STATUS_SHOW = os.environ.get('PROGRESS_STATUS_SHOW', '10')
        self.MAX_CONCURRENT_TASKS = os.environ.get('MAX_CONCURRENT_TASKS', '4')
        self.WORKERS = os.environ.get('WORKERS', '4')
        self.MAX_CONCURRENT_TRANSMISSIONS = os.environ.get('MAX_CONCURRENT_TRANSMISSIONS', '4')

    def validate_env(self):
        if not self.API_ID or not self.API_HASH or not self.BOT_TOKEN or not self.AUTHORIZED_USER_ID:
            return False
        return True
