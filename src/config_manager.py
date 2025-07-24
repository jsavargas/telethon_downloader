import configparser
import os

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
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
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def get_download_path(self, extension):
        self._load_config() # Re-read config.ini to pick up new paths
        return self.config.get('EXTENSIONS', extension.lower(), fallback=None)