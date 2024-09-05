import os

import logger


class EnvironmentReader:
    def __init__(self):
        # Define some variables so the code reads easier
        self.API_ID = os.environ.get("TG_API_ID")
        self.API_HASH = os.environ.get("TG_API_HASH")
        self.BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
        self.SESSION = os.environ.get("TG_SESSION", "bottorrent")

        self.PUID = os.environ.get("PUID", None)
        self.PGID = os.environ.get("PGID", None)

        self.PERMISSIONS_FOLDER = os.environ.get("PERMISSIONS_FOLDER", 777)
        self.PERMISSIONS_FILE = os.environ.get("PERMISSIONS_FILE", 755)

        self.TG_AUTHORIZED_USER_ID = os.environ.get("TG_AUTHORIZED_USER_ID", False)
        self.TG_MAX_PARALLEL = int(os.environ.get("TG_MAX_PARALLEL", 4))
        self.TG_PROGRESS_DOWNLOAD = os.environ.get("TG_PROGRESS_DOWNLOAD", True)
        self.PROGRESS_STATUS_SHOW = os.environ.get("PROGRESS_STATUS_SHOW", 10)
        self.TG_DOWNLOAD_PATH = os.environ.get("TG_DOWNLOAD_PATH", "/download")
        self.TG_DOWNLOAD_PATH_TORRENTS = os.environ.get("TG_DOWNLOAD_PATH_TORRENTS", "/watch")  # fmt: skip

        self.PATH_COMPLETED = os.path.join(self.TG_DOWNLOAD_PATH, "completed")
        self.PATH_LINKS = os.path.join(self.TG_DOWNLOAD_PATH, "links")
        self.PATH_TMP = os.path.join(self.TG_DOWNLOAD_PATH, "tmp")

        ## YOUTUBE
        self.PATH_YOUTUBE = os.path.join(self.TG_DOWNLOAD_PATH, "youtube")
        self.YOUTUBE_AUDIO_FOLDER = os.environ.get("YOUTUBE_AUDIO_FOLDER", os.path.join(self.PATH_YOUTUBE, "youtube_audios"))  # fmt: skip
        self.YOUTUBE_VIDEO_FOLDER = os.environ.get("YOUTUBE_VIDEO_FOLDER", os.path.join(self.PATH_YOUTUBE, "youtube_video"))  # fmt: skip

        self.YOUTUBE_LINKS_SUPPORTED = os.environ.get(
            "YOUTUBE_LINKS_SUPPORTED", "youtube.com,youtu.be"
        )
        self.YOUTUBE_DEFAULT_DOWNLOAD = os.environ.get(
            "YOUTUBE_DEFAULT_DOWNLOAD", "VIDEO"
        )
        self.YOUTUBE_DEFAULT_EXTENSION = os.environ.get(
            "YOUTUBE_DEFAULT_EXTENSION", "mkv"
        )
        self.YOUTUBE_FORMAT_AUDIO = os.environ.get(
            "YOUTUBE_FORMAT_AUDIO", "bestaudio/best"
        )  # best
        self.YOUTUBE_FORMAT_VIDEO = os.environ.get(
            "YOUTUBE_FORMAT_VIDEO", "bestvideo+bestaudio/best"
        )  # best
        self.YOUTUBE_SHOW_OPTION_TIMEOUT = int(
            os.environ.get("YOUTUBE_SHOW_OPTION_TIMEOUT", 5)
        )
        self.YOUTUBE_SHOW_OPTION = os.environ.get("YOUTUBE_SHOW_OPTION", True)

        ## TELEGRAM
        self.TG_DL_TIMEOUT = int(os.environ.get("TG_DL_TIMEOUT", 3600))
        self.TG_FOLDER_BY_AUTHORIZED = os.environ.get("TG_FOLDER_BY_AUTHORIZED", False)
        self.TG_UNZIP_TORRENTS = os.environ.get("TG_UNZIP_TORRENTS", False)
        self.ENABLED_UNZIP = os.environ.get("ENABLED_UNZIP", False)
        self.ENABLED_UNRAR = os.environ.get("ENABLED_UNRAR", False)
        self.ENABLED_7Z = os.environ.get("ENABLED_7Z", False)

        self.LANGUAGE = os.environ.get("APP_LANGUAGE", "en_EN")

        self.PATH_CONFIG = "/config/config.ini"
        self.PATH_PENDING_MESSAGES = "/config/pending_messages.json"
        self.PATH_DOWNLOAD_FILES = "/config/download_files.json"

        self.YOUTUBE = "youtube"

    def print_variables(self):
        logger.logger.info(f"API_ID: {self.API_ID}")
        logger.logger.info(f"API_HASH: {self.API_HASH}")
        logger.logger.info(f"BOT_TOKEN: {self.BOT_TOKEN}")
        logger.logger.info(f"SESSION: {self.SESSION}")

    def printAttribute(self, attribute_name):
        if hasattr(self, attribute_name):
            attribute_value = getattr(self, attribute_name)
            logger.logger.info(f"{attribute_name}: {attribute_value}")
        else:
            attribute_value = getattr(self, attribute_name)
            logger.logger.info(f"{attribute_name}: {attribute_value}")

    def get_variable(self, variable_name):
        value = getattr(self, variable_name, None)
        if isinstance(value, str):
            return value.strip() if value is not None else None
        return value
