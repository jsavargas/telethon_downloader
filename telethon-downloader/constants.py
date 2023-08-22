import os

from logger import logger


# Define some variables so the code reads easier
API_ID = os.environ.get('TG_API_ID')
API_HASH = os.environ.get('TG_API_HASH')
BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
SESSION = os.environ.get('TG_SESSION', 'bottorrent')

TG_AUTHORIZED_USER_ID = os.environ.get('TG_AUTHORIZED_USER_ID', False)
TG_MAX_PARALLEL = int(os.environ.get('TG_MAX_PARALLEL',4))
TG_PROGRESS_DOWNLOAD =  os.environ.get('TG_PROGRESS_DOWNLOAD', True)
PROGRESS_STATUS_SHOW =  os.environ.get('PROGRESS_STATUS_SHOW', 50)

TG_DOWNLOAD_PATH = os.environ.get('TG_DOWNLOAD_PATH', '/download')
TG_DOWNLOAD_PATH_TORRENTS = os.environ.get('TG_DOWNLOAD_PATH_TORRENTS', '/watch')
PATH_YOUTUBE = os.path.join(TG_DOWNLOAD_PATH,'youtube')
PATH_TMP = os.path.join(TG_DOWNLOAD_PATH,'tmp')
PATH_COMPLETED = os.path.join(TG_DOWNLOAD_PATH,'completed')


YOUTUBE_ASK = os.environ.get('YOUTUBE_ASK', True)
YOUTUBE_LINKS_SOPORTED = os.environ.get('YOUTUBE_LINKS_SOPORTED', 'youtube.com,youtu.be')
YOUTUBE_FORMAT = os.environ.get('YOUTUBE_FORMAT', 'bestvideo+bestaudio/best')  #best
TG_DL_TIMEOUT = int(os.environ.get('TG_DL_TIMEOUT',3600))

TG_UNZIP_TORRENTS = os.environ.get('TG_UNZIP_TORRENTS', False)
TG_FOLDER_BY_AUTHORIZED = os.environ.get('TG_FOLDER_BY_AUTHORIZED', False)




PATH_CONFIG = '/config/config.ini'

YOUTUBE = 'youtube'