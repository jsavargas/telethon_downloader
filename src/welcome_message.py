import time
import sys
from telethon import __version__ as telethon_version

class WelcomeMessage:
    def __init__(self, versions, env_config, logger, download_manager):
        self.versions = versions
        self.env_config = env_config
        self.logger = logger
        self.download_manager = download_manager

    def log_welcome_message(self):
        try:
            self.logger.info(f"Starting Telegram Downloader Bot Started : {time.strftime('%Y/%m/%d %H:%M:%S')}")
            self.logger.info(f"PYTHON_VERSION                : {sys.version.split(' ')[0]}")
            self.logger.info(f"BOT_VERSION                   : {self.versions.bot_version}")
            self.logger.info(f"TELETHON_VERSION              : {self.versions.telethon_version}")
            self.logger.info(f"YT_DLP_VERSION                : {self.versions.yt_dlp_version}")
            self.logger.info(f"API_ID                        : {self.env_config.API_ID[:3]}***") # Masking part of the ID
            self.logger.info(f"API_HASH                      : {self.env_config.API_HASH[:5]}****************") # Masking part of the hash
            self.logger.info(f"BOT_TOKEN                     : {self.env_config.BOT_TOKEN[:10]}***********************") # Masking part of the token
            self.logger.info(f"AUTHORIZED_USER_ID            : {self.env_config.AUTHORIZED_USER_ID.split(',')}")
            self.logger.info(f"DOWNLOAD_DIR                  : {self.env_config.BASE_DOWNLOAD_PATH}")
            self.logger.info(f"DOWNLOAD_INCOMPLETED_PATH     : {self.download_manager.default_incompleted_dir}")
            self.logger.info(f"DOWNLOAD_COMPLETED_PATH       : {self.download_manager.default_completed_dir}")        
            self.logger.info(f"YOUTUBE_VIDEO_FOLDER          : {self.env_config.YOUTUBE_VIDEO_FOLDER}")        
            self.logger.info(f"YOUTUBE_AUDIO_FOLDER          : {self.env_config.YOUTUBE_AUDIO_FOLDER}")        
            self.logger.info(f"DOWNLOAD_PATH_TORRENTS        : {self.download_manager.torrent_path}")
            self.logger.info(f"PROGRESS_DOWNLOAD             : {self.env_config.PROGRESS_DOWNLOAD}")
            self.logger.info(f"PROGRESS_STATUS_SHOW          : {self.env_config.PROGRESS_STATUS_SHOW}")
            self.logger.info(f"MAX_CONCURRENT_TASKS          : {self.env_config.MAX_CONCURRENT_TASKS}")
            self.logger.info(f"TORRENT_MODE                  : {self.env_config.TORRENT_MODE}")
        except Exception as e:
            self.logger.error(f"Error logging welcome message: {e}")

    def get_message(self):
        try:
            return (
                f"**Telegram Downloader Bot Started**\n\n"
                f"**python version:** {sys.version.split(' ')[0]}\n"
                f"**bot version:** {self.versions.bot_version}\n"
                f"**teleton version:** {self.versions.telethon_version}\n"
                f"**yt-dlp version:** {self.versions.yt_dlp_version}"
            )
        except Exception as e:
            self.logger.error(f"Error generating welcome message: {e}")
            return "Error generating welcome message."