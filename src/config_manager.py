import configparser
import os

class ConfigManager:
    def __init__(self, config_path, logger, puid=None, pgid=None):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.logger = logger
        self.puid = puid
        self.pgid = pgid
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            # Create a default config if it doesn't exist
            self._create_default_config()

    def _create_default_config(self):
        self.config['EXTENSIONS'] = {
            'pdf': '/download/pdf',
            'cbr': '/download/pdf',
            'mp3': '/download/mp3',
            'flac': '/download/mp3',
            'jpg': '/download/jpg',
            'mp4': '/download/mp4',
        }
        self.config['GROUP_PATH'] = {
            '-10012345789': '/download/1001234577',
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
        
        # Set permissions and ownership for config.ini
        if self.puid is not None and self.pgid is not None:
            try:
                os.chown(self.config_path, int(self.puid), int(self.pgid))
                self.logger.info(f"Changed ownership of {self.config_path} to {int(self.puid)}:{int(self.pgid)}")
            except Exception as e:
                self.logger.error(f"Error changing ownership of {self.config_path}: {e}")
        try:
            os.chmod(self.config_path, 0o644) # Set permissions for config.ini
            self.logger.info(f"Changed permissions of {self.config_path} to 0o644")
        except Exception as e:
            self.logger.error(f"Error changing permissions of {self.config_path}: {e}")

    def get_download_path(self, extension):
        self._load_config() # Re-read config.ini to pick up new paths
        return self.config.get('EXTENSIONS', extension.lower(), fallback=None)

    def get_group_path(self, group_id):
        self._load_config() # Re-read config.ini to pick up new paths
        return self.config.get('GROUP_PATH', str(group_id), fallback=None)
