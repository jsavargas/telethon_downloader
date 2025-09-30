import configparser
import os

class ConfigManager:
    def __init__(self, config_dir, logger, puid=None, pgid=None):
        self.config_dir = config_dir
        self.config_path = os.path.join(config_dir, 'config.ini')
        self.config = configparser.ConfigParser()
        self.logger = logger
        self.puid = puid
        self.pgid = pgid
        try:
            self._load_config()
        except Exception as e:
            self.logger.error(f"Error initializing ConfigManager: {e}")

    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path)
                # Check if GROUP_PATH section exists, if not, add it
                if 'GROUP_PATH' not in self.config:
                    self.config['GROUP_PATH'] = {
                        '-10012345789': '/download/1001234577',
                    }
                    self._write_config()
                    self.logger.info(f"Added [GROUP_PATH] section to {self.config_path}")
                # Check if EXTENSIONS section exists, if not, add it
                if 'EXTENSIONS' not in self.config:
                    self.config['EXTENSIONS'] = {
                        'pdf': '/download/pdf',
                        'cbr': '/download/pdf',
                        'mp3': '/download/mp3',
                        'flac': '/download/mp3',
                        'jpg': '/download/jpg',
                        'mp4': '/download/mp4',
                    }
                    self._write_config()
                    self.logger.info(f"Added [EXTENSIONS] section to {self.config_path}")
                # Check if KEYWORDS section exists, if not, add it
                if 'KEYWORDS' not in self.config:
                    self.config['KEYWORDS'] = {
                        'tanganana': '/download/tanganana',
                    }
                    self._write_config()
                    self.logger.info(f"Added [KEYWORDS] section to {self.config_path}")
                # Check if REGEX_PATH section exists, if not, add it
                if 'REGEX_PATH' not in self.config:
                    self.config['REGEX_PATH'] = {
                        '/example/i': '/download/example',
                    }
                    self._write_config()
                    self.logger.info(f"Added [REGEX_PATH] section to {self.config_path}")
                # Check if REMOVE_PATTERNS section exists, if not, add it
                if 'REMOVE_PATTERNS' not in self.config:
                    self.config['REMOVE_PATTERNS'] = {
                        '*': 'tif_,[tof_,0001',
                        '-100123456': 'tif_',
                    }
                    self._write_config()
                    self.logger.info(f"Added [REMOVE_PATTERNS] section to {self.config_path}")
            else:
                # Create a default config if it doesn't exist
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")

    def _write_config(self):
        try:
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
        except Exception as e:
            self.logger.error(f"Error writing config: {e}")

    def _create_default_config(self):
        try:
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
            self.config['KEYWORDS'] = {
                'tanganana': '/download/tanganana',
            }
            self.config['REGEX_PATH'] = {
                '/example/i': '/download/example',
            }
            self.config['REMOVE_PATTERNS'] = {
                '*': 'tif_,[tof_,0001',
                '100123456': '2025',
            }
            self._write_config()
        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")

    def get_download_path(self, extension):
        try:
            self._load_config() # Re-read config.ini to pick up new paths
            return self.config.get('EXTENSIONS', extension.lower(), fallback=None)
        except Exception as e:
            self.logger.error(f"Error getting download path for extension {extension}: {e}")
            return None

    def get_group_path(self, channel_id):
        try:
            self._load_config() # Re-read config.ini to pick up new paths
            return self.config.get('GROUP_PATH', str(channel_id), fallback=None)
        except Exception as e:
            self.logger.error(f"Error getting group path for channel ID {channel_id}: {e}")
            return None

    def get_keyword_path(self, keyword):
        try:
            self._load_config() # Re-read config.ini to pick up new paths
            return self.config.get('KEYWORDS', keyword.lower(), fallback=None)
        except Exception as e:
            self.logger.error(f"Error getting keyword path for keyword {keyword}: {e}")
            return None

    def get_all_keywords(self):
        try:
            self._load_config() # Re-read config.ini to pick up new paths
            if 'KEYWORDS' in self.config:
                return {k: v for k, v in self.config.items('KEYWORDS')}
            return {}
        except Exception as e:
            self.logger.error(f"Error getting all keywords: {e}")
            return {}

    def get_all_regex_paths(self):
        try:
            self._load_config() # Re-read config.ini to pick up new paths
            if 'REGEX_PATH' in self.config:
                return {k: v for k, v in self.config.items('REGEX_PATH')}
            return {}
        except Exception as e:
            self.logger.error(f"Error getting all regex paths: {e}")
            return {}

    def get_remove_patterns(self, group_id=None):
        try:
            self._load_config()
            if 'REMOVE_PATTERNS' not in self.config:
                return []
            if (value := self.config.get('REMOVE_PATTERNS', str(group_id), fallback=None)) \
                or (value := self.config.get('REMOVE_PATTERNS', '*', fallback=None)):
                self.logger.info(f"get_remove_patterns remove_patterns_section {value} group_id {group_id}")
            else:
                return []
            return [v.strip() for v in value.split(',') if v.strip()]
        except Exception as e:
            self.logger.error(f"Error getting remove patterns for group {group_id}: {e}")
            return []

    def add_extension_path(self, extension, path):
        try:
            if 'EXTENSIONS' not in self.config:
                self.config['EXTENSIONS'] = {}
            self.config['EXTENSIONS'][extension.lower()] = path
            self._write_config()
            self.logger.info(f"Added/Updated extension path: {extension.lower()} = {path}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding extension path for {extension}: {e}")
            return False