import time
from telethon import __version__ as telethon_version

class WelcomeMessage:
    def __init__(self, versions, env_config, logger, download_manager):
        self.versions = versions
        self.env_config = env_config
        self.logger = logger
        self.download_manager = download_manager

    def log_welcome_message(self):
        self.logger.info(f"Starting Telegram Downloader Bot Started : {time.strftime('%Y/%m/%d %H:%M:%S')}")
        self.logger.info(f"BOT_VERSION                   : {self.versions.bot_version}")
        self.logger.info(f"TELETHON_VERSION              : {self.versions.telethon_version}")
        self.logger.info(f"YTDLP_VERSION                 : {self.env_config.YTDLP_VERSION}")
        self.logger.info(f"API_ID                        : {self.env_config.API_ID[:3]}***") # Masking part of the ID
        self.logger.info(f"API_HASH                      : {self.env_config.API_HASH[:5]}****************") # Masking part of the hash
        self.logger.info(f"BOT_TOKEN                     : {self.env_config.BOT_TOKEN[:10]}***********************") # Masking part of the token
        self.logger.info(f"AUTHORIZED_USER_ID            : {self.env_config.AUTHORIZED_USER_ID.split(',')}")
        self.logger.info(f"DOWNLOAD_DIR                  : {self.env_config.BASE_DOWNLOAD_PATH}")
        self.logger.info(f"DOWNLOAD_INCOMPLETED_PATH     : {self.download_manager.default_incompleted_dir}")
        self.logger.info(f"DOWNLOAD_COMPLETED_PATH       : {self.download_manager.default_completed_dir}")
        # Assuming DOWNLOAD_PATH_TORRENTS is not directly from env_config, if it is, add it to env_config
        # self.logger.info(f"DOWNLOAD_PATH_TORRENTS        : {self.env_config.DOWNLOAD_PATH_TORRENTS}")
        self.logger.info(f"PROGRESS_DOWNLOAD             : {self.env_config.PROGRESS_DOWNLOAD}")
        self.logger.info(f"PROGRESS_STATUS_SHOW          : {self.env_config.PROGRESS_STATUS_SHOW}")
        self.logger.info(f"MAX_CONCURRENT_TASKS          : {self.env_config.MAX_CONCURRENT_TASKS}")
        self.logger.info(f"WORKERS                       : {self.env_config.WORKERS}")
        self.logger.info(f"MAX_CONCURRENT_TRANSMISSIONS  : {self.env_config.MAX_CONCURRENT_TRANSMISSIONS}")

    def get_message(self):
        return (
            f"Telegram Downloader Bot Started\n\n"
            f"bot version: {self.versions.bot_version}\n"
            f"teleton version: {self.versions.telethon_version}"
        )
