import os

import logger

class EnvironmentReader:
    def __init__(self):

        # Define some variables so the code reads easier
        self.API_ID = os.environ.get('TG_API_ID')
        self.API_HASH = os.environ.get('TG_API_HASH')
        self.BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
        self.SESSION = os.environ.get('TG_SESSION', 'bottorrent')

        self.PUID = os.environ.get('PUID')
        self.PGID = os.environ.get('PGID')

        self.TG_AUTHORIZED_USER_ID = os.environ.get('TG_AUTHORIZED_USER_ID', False)
        self.TG_MAX_PARALLEL = int(os.environ.get('TG_MAX_PARALLEL',4))
        self.TG_PROGRESS_DOWNLOAD =  os.environ.get('TG_PROGRESS_DOWNLOAD', True)
        self.PROGRESS_STATUS_SHOW =  os.environ.get('PROGRESS_STATUS_SHOW', 50)

        self.TG_DOWNLOAD_PATH = os.environ.get('TG_DOWNLOAD_PATH', '/download')
        self.PATH_COMPLETED = os.path.join(self.TG_DOWNLOAD_PATH,'completed')
        self.PATH_YOUTUBE = os.path.join(self.TG_DOWNLOAD_PATH,'youtube')
        self.YOUTUBE_AUDIOS_FOLDER = os.path.join(self.TG_DOWNLOAD_PATH,'youtube_audios')
        self.TG_DOWNLOAD_PATH_TORRENTS = os.environ.get('TG_DOWNLOAD_PATH_TORRENTS', '/watch')
        self.PATH_LINKS = os.path.join(self.TG_DOWNLOAD_PATH,'links')
        self.PATH_TMP = os.path.join(self.TG_DOWNLOAD_PATH,'tmp')


        self.YOUTUBE_LINKS_SOPORTED = os.environ.get('YOUTUBE_LINKS_SOPORTED', 'youtube.com,youtu.be')
        self.YOUTUBE_DEFAULT_DOWNLOAD = os.environ.get('YOUTUBE_DEFAULT_DOWNLOAD', 'VIDEO')
        self.YOUTUBE_FORMAT_AUDIO = os.environ.get('YOUTUBE_FORMAT_AUDIO', 'bestaudio/best')  #best
        self.YOUTUBE_FORMAT_VIDEO = os.environ.get('YOUTUBE_FORMAT_VIDEO', 'bestvideo+bestaudio/best')  #best
        self.YOUTUBE_TIMEOUT_OPTION = int(os.environ.get('YOUTUBE_TIMEOUT_OPTION',5))
        self.YOUTUBE_SHOW_OPTION = os.environ.get('YOUTUBE_SHOW_OPTION', True)

        self.TG_DL_TIMEOUT = int(os.environ.get('TG_DL_TIMEOUT',3600))

        self.TG_UNZIP_TORRENTS = os.environ.get('TG_UNZIP_TORRENTS', False)
        self.TG_FOLDER_BY_AUTHORIZED = os.environ.get('TG_FOLDER_BY_AUTHORIZED', False)


        self.LANGUAGE = os.environ.get('APP_LANGUAGE', 'en_EN')

        self.PATH_CONFIG = '/config/config.ini'

        self.YOUTUBE = 'youtube'


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




