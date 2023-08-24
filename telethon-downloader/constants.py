import os

from logger import logger


# Define some variables so the code reads easier
API_ID = os.environ.get('TG_API_ID')
API_HASH = os.environ.get('TG_API_HASH')
BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
SESSION = os.environ.get('TG_SESSION', 'bottorrent')

PUID = os.environ.get('PUID')
PGID = os.environ.get('PGID')

TG_AUTHORIZED_USER_ID = os.environ.get('TG_AUTHORIZED_USER_ID', False)
TG_MAX_PARALLEL = int(os.environ.get('TG_MAX_PARALLEL',4))
TG_PROGRESS_DOWNLOAD =  os.environ.get('TG_PROGRESS_DOWNLOAD', True)
PROGRESS_STATUS_SHOW =  os.environ.get('PROGRESS_STATUS_SHOW', 50)

TG_DOWNLOAD_PATH = os.environ.get('TG_DOWNLOAD_PATH', '/download')
TG_DOWNLOAD_PATH_TORRENTS = os.environ.get('TG_DOWNLOAD_PATH_TORRENTS', '/watch')
PATH_YOUTUBE = os.path.join(TG_DOWNLOAD_PATH,'youtube')
YOUTUBE_AUDIOS_FOLDER = os.path.join(TG_DOWNLOAD_PATH,'youtube_audios')
PATH_TMP = os.path.join(TG_DOWNLOAD_PATH,'tmp')
PATH_COMPLETED = os.path.join(TG_DOWNLOAD_PATH,'completed')


YOUTUBE_LINKS_SOPORTED = os.environ.get('YOUTUBE_LINKS_SOPORTED', 'youtube.com,youtu.be')
YOUTUBE_DEFAULT_DOWNLOAD = os.environ.get('YOUTUBE_DEFAULT_DOWNLOAD', 'VIDEO')
YOUTUBE_FORMAT_AUDIO = os.environ.get('YOUTUBE_FORMAT_AUDIO', 'bestaudio/best')  #best
YOUTUBE_FORMAT_VIDEO = os.environ.get('YOUTUBE_FORMAT_VIDEO', 'bestvideo+bestaudio/best')  #best
YOUTUBE_TIMEOUT_OPTION = int(os.environ.get('YOUTUBE_TIMEOUT_OPTION',5))
YOUTUBE_SHOW_OPTION = os.environ.get('YOUTUBE_SHOW_OPTION', True)

TG_DL_TIMEOUT = int(os.environ.get('TG_DL_TIMEOUT',3600))

TG_UNZIP_TORRENTS = os.environ.get('TG_UNZIP_TORRENTS', False)
TG_FOLDER_BY_AUTHORIZED = os.environ.get('TG_FOLDER_BY_AUTHORIZED', False)


LANGUAGE = os.environ.get('APP_LANGUAGE', 'en_EN')

PATH_CONFIG = '/config/config.ini'

YOUTUBE = 'youtube'