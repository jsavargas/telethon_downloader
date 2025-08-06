import os
import logging

class EnvConfig:
    def __init__(self, logger):
        self.logger = logger
        try:
            self.API_ID = os.environ.get("API_ID") or os.environ.get("TG_API_ID")
            self.API_HASH = os.environ.get("API_HASH") or os.environ.get("TG_API_HASH")
            self.BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TG_BOT_TOKEN")
            self.AUTHORIZED_USER_ID = os.environ.get("AUTHORIZED_USER_ID") or os.environ.get("TG_AUTHORIZED_USER_ID")
            self.BASE_DOWNLOAD_PATH = os.environ.get("TG_DOWNLOAD_PATH") or os.environ.get("DOWNLOAD_PATH", '/download')
            self.DOWNLOAD_PATH_TORRENTS = os.environ.get('DOWNLOAD_PATH_TORRENTS', '/watch')
            self.YOUTUBE_VIDEO_FOLDER = os.environ.get('YOUTUBE_VIDEO_FOLDER', os.path.join(self.BASE_DOWNLOAD_PATH, "youtube", "videos"))
            self.YOUTUBE_AUDIO_FOLDER = os.environ.get('YOUTUBE_AUDIO_FOLDER', os.path.join(self.BASE_DOWNLOAD_PATH, "youtube", "audios"))
            self.YOUTUBE_FORMAT_VIDEO = os.environ.get('YOUTUBE_FORMAT_VIDEO', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best')
            self.YOUTUBE_FORMAT_AUDIO = os.environ.get('YOUTUBE_FORMAT_AUDIO', 'bestaudio/best')
            self.PATH_CONFIG = os.environ.get("PATH_CONFIG", '/config/')
            self.PUID = os.environ.get('PUID')
            self.PGID = os.environ.get('PGID')
            self.YTDLP_VERSION = os.environ.get('YTDLP_VERSION', 'N/A')
            self.PROGRESS_DOWNLOAD =  os.environ.get("TG_PROGRESS_DOWNLOAD") or os.environ.get('PROGRESS_DOWNLOAD', 'True')
            self.PROGRESS_STATUS_SHOW = os.environ.get('PROGRESS_STATUS_SHOW', '10')
            self.MAX_CONCURRENT_TASKS = os.environ.get("TG_MAX_PARALLEL") or os.environ.get('MAX_CONCURRENT_TASKS', '4')
            self.YOUTUBE_TIMEOUT_OPTION = int(os.environ.get('YOUTUBE_TIMEOUT_OPTION', '5'))
            self.YOUTUBE_DEFAULT_DOWNLOAD = os.environ.get('YOUTUBE_DEFAULT_DOWNLOAD', 'video').lower()
            self.TORRENT_MODE = os.environ.get('TORRENT_MODE', 'watch').lower()
            self.QBT_HOST = os.environ.get('QBT_HOST')
            self.QBT_PORT = os.environ.get('QBT_PORT','8080')
            self.QBT_USERNAME = os.environ.get('QBT_USERNAME')
            self.QBT_PASSWORD = os.environ.get('QBT_PASSWORD')
        except Exception as e:
            self.logger.error(f"Error initializing EnvConfig: {e}")

    def validate_env(self):
        try:
            if not self.API_ID or not self.API_HASH or not self.BOT_TOKEN or not self.AUTHORIZED_USER_ID:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error validating environment variables: {e}")
            return False
