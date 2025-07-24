import os

class EnvConfig:
    def __init__(self):
        self.API_ID = os.environ.get("API_ID") or os.environ.get("TG_API_ID")
        self.API_HASH = os.environ.get("API_HASH") or os.environ.get("TG_API_HASH")
        self.BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TG_BOT_TOKEN")
        self.AUTHORIZED_USER_ID = os.environ.get("AUTHORIZED_USER_ID") or os.environ.get("TG_AUTHORIZED_USER_ID")
        self.BASE_DOWNLOAD_PATH = os.environ.get("TG_DOWNLOAD_PATH") or os.environ.get("DOWNLOAD_PATH", '/download')
        self.PATH_CONFIG = os.environ.get("PATH_CONFIG", '/config/config.ini')

    def validate_env(self):
        if not self.API_ID or not self.API_HASH or not self.BOT_TOKEN or not self.AUTHORIZED_USER_ID:
            return False
        return True