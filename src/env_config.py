import os
import logging

class EnvConfig:
    def __init__(self, logger):
        self.logger = logger
        try:
            self.API_ID = (os.environ.get("API_ID") or os.environ.get("TG_API_ID") or "").strip()
            self.API_HASH = (os.environ.get("API_HASH") or os.environ.get("TG_API_HASH") or "").strip()
            self.BOT_TOKEN = (os.environ.get("BOT_TOKEN") or os.environ.get("TG_BOT_TOKEN") or "").strip()
            self.AUTHORIZED_USER_ID = (os.environ.get("AUTHORIZED_USER_ID") or os.environ.get("TG_AUTHORIZED_USER_ID") or "").strip()
            self.BASE_DOWNLOAD_PATH = (os.environ.get("TG_DOWNLOAD_PATH") or os.environ.get("DOWNLOAD_PATH", '/download')).strip()
            self.DOWNLOAD_PATH_TORRENTS = os.environ.get('DOWNLOAD_PATH_TORRENTS', '/watch').strip()
            self.YOUTUBE_VIDEO_FOLDER = os.environ.get('YOUTUBE_VIDEO_FOLDER', os.path.join(self.BASE_DOWNLOAD_PATH, "youtube", "videos")).strip()
            self.YOUTUBE_AUDIO_FOLDER = os.environ.get('YOUTUBE_AUDIO_FOLDER', os.path.join(self.BASE_DOWNLOAD_PATH, "youtube", "audios")).strip()
            self.YOUTUBE_FORMAT_VIDEO = os.environ.get('YOUTUBE_FORMAT_VIDEO', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best').strip()
            self.YOUTUBE_FORMAT_AUDIO = os.environ.get('YOUTUBE_FORMAT_AUDIO', 'bestaudio/best').strip()
            self.PATH_CONFIG = os.environ.get("PATH_CONFIG", '/config/').strip()
            self.PUID = (os.environ.get('PUID') or "").strip()
            self.PGID = (os.environ.get('PGID') or "").strip()
            self.YTDLP_VERSION = os.environ.get('YTDLP_VERSION', 'N/A').strip()
            self.PROGRESS_DOWNLOAD =  (os.environ.get("TG_PROGRESS_DOWNLOAD") or os.environ.get('PROGRESS_DOWNLOAD', 'True')).strip()
            self.PROGRESS_STATUS_SHOW = os.environ.get('PROGRESS_STATUS_SHOW', '10').strip()
            self.MAX_CONCURRENT_TASKS = (os.environ.get("TG_MAX_PARALLEL") or os.environ.get('MAX_CONCURRENT_TASKS', '4')).strip()
            self.YOUTUBE_TIMEOUT_OPTION = int((os.environ.get('YOUTUBE_TIMEOUT_OPTION', '5')).strip())
            self.YOUTUBE_DEFAULT_DOWNLOAD = (os.environ.get('YOUTUBE_DEFAULT_DOWNLOAD', 'video').strip()).lower()
            self.TORRENT_MODE = (os.environ.get('TORRENT_MODE', 'watch').strip()).lower()
            self.QBT_HOST = (os.environ.get('QBT_HOST') or "").strip()
            self.QBT_PORT = (os.environ.get('QBT_PORT','8080')).strip()
            self.QBT_USERNAME = (os.environ.get('QBT_USERNAME') or "").strip()
            self.QBT_PASSWORD = (os.environ.get('QBT_PASSWORD') or "").strip()
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
