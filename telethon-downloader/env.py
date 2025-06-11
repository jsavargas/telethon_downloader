import os
from dotenv import load_dotenv

load_dotenv()

class Env:
    def __init__(self):

        self.API_ID = os.getenv('TG_API_ID') or os.getenv('API_ID')
        self.API_HASH = os.getenv('TG_API_HASH') or os.getenv('API_HASH')
        self.BOT_TOKEN = os.getenv('TG_BOT_TOKEN') or os.getenv('BOT_TOKEN')      
        # Handling both AUTHORIZED_USER_ID and TG_AUTHORIZED_USER_ID
        AUTHORIZED_USER_IDS = os.getenv('TG_AUTHORIZED_USER_ID') or os.getenv('AUTHORIZED_USER_ID', 'me')
        self.AUTHORIZED_USER_ID = AUTHORIZED_USER_IDS.replace(" ", "").split(",")
        self.PUID = int(os.getenv('PUID', '1001'))
        self.PGID = int(os.getenv('PGID', '1001'))
        #self.MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '3'))

        self.MAX_CONCURRENT_TASKS = os.getenv('TG_MAX_PARALLEL') or int(os.getenv('MAX_CONCURRENT_TASKS', '3'))

        self.WORKERS = int(os.getenv('WORKERS', '4'))
        self.MAX_CONCURRENT_TRANSMISSIONS = int(os.getenv('MAX_CONCURRENT_TRANSMISSIONS', '4'))
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '4'))
        self.PROGRESS_STATUS_SHOW = int(os.getenv('PROGRESS_STATUS_SHOW', '10'))

        self.IS_DELETE = os.getenv('IS_DELETE', False)
        self.IS_DELETE = bool(self.IS_DELETE) if isinstance(self.IS_DELETE, str) and self.IS_DELETE.lower() in ["true", "1"] else self.IS_DELETE
        self.MESSAGE_FILE = os.getenv('MESSAGE_FILE', 'False').lower() in ('true', '1')
        self.PROGRESS_DOWNLOAD = os.getenv('PROGRESS_DOWNLOAD', 'True').strip().lower() in ('true', '1')

        self.CONFIG_PATH = os.environ.get("CONFIG_PATH", "/config")
        self.DOWNLOAD_PATH = os.environ.get("DOWNLOAD_PATH", "/download")
        self.DOWNLOAD_COMPLETED_PATH = os.path.join(self.DOWNLOAD_PATH, "completed")
        self.DOWNLOAD_INCOMPLETED_PATH = os.path.join(self.DOWNLOAD_PATH, "incompleted")
        self.DOWNLOAD_PATH_TORRENTS = os.environ.get("DOWNLOAD_PATH_TORRENTS", "/watch")  # fmt: skip

        self.DOWNLOAD_FILES_DB = os.environ.get("DOWNLOAD_FILES_DB", os.path.join(self.CONFIG_PATH, "download_files_db.json"))  # fmt: skip
        self.PENDING_FILES_DB = os.environ.get("PENDING_FILES_DB", os.path.join(self.CONFIG_PATH, "pending_messages.json"))  # fmt: skip
        
        self.WELCOME="WELCOME"



    