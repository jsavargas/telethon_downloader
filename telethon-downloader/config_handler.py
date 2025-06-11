import os
import configparser
from env import Env
from info_handler import InfoMessages
from logger_config import logger

from enum import Enum

class ConfigKeys(Enum):
    DEFAULT = "DEFAULT"
    EXTENSIONS = "EXTENSIONS"
    GROUP_PATH = "GROUP_PATH"
    RENAME_GROUP = "RENAME_GROUP"
    KEYWORDS = "KEYWORDS"
    REGEX_RENAME = "REGEX_RENAME"
    REMOVE_PATTERNS = "REMOVE_PATTERNS"
    SETTINGS = "SETTINGS"

class DefaultPath:
    def __init__(self):
        self.env = Env()
        self.default = {'default_path': os.getenv('DEFAULT_PATH', self.env.DOWNLOAD_COMPLETED_PATH)}
        self.extensions = {'jpg': '/download/images'}
        self.rename_group = {'-100123456': 'yes'}
        self.keywords = {'tanganana': '/download/tanganana'}
        self.group_paths = {'-100123456': '/download/100123456'}
        self.regex_rename = {'-100123456': '/old_text/new_text/'}
        self.remove_patterns = {'-100123456': '[tif_', 'pattern1': '[tif_', 'pattern2': '[tof_'}
        self.settings = {'chars_to_replace ': '|/'}


class ConfigHandler:
    def __init__(self):
        self.env = Env()
        self.info_handler = InfoMessages()
        self.path = DefaultPath()
        self.config_file = os.path.join(self.env.CONFIG_PATH, "config.ini")
        self.config = self._initialize_config()
        self.config.read(self.config_file)
    
    
    def _create_default_config(self, config):
        if not os.path.exists(self.config_file):
            config[ConfigKeys.DEFAULT.value] = self.path.default
            config[ConfigKeys.EXTENSIONS.value] = self.path.extensions
            config[ConfigKeys.GROUP_PATH.value] = self.path.group_paths
            config[ConfigKeys.RENAME_GROUP.value] = self.path.rename_group
            config[ConfigKeys.KEYWORDS.value] = self.path.keywords
            config[ConfigKeys.REGEX_RENAME.value] = self.path.regex_rename
            config[ConfigKeys.REMOVE_PATTERNS.value] = self.path.remove_patterns
            config[ConfigKeys.SETTINGS.value] = self.path.settings
            with open(self.config_file, 'w') as configfile:
                config.write(configfile)
            return config

    def _initialize_config(self):
        config = configparser.ConfigParser()
        if not config.read(self.config_file):
            config = self._create_default_config(config)

        config = self.createNewSection(config, ConfigKeys.EXTENSIONS.value, self.path.extensions)        
        config = self.createNewSection(config, ConfigKeys.GROUP_PATH.value, self.path.group_paths)        
        config = self.createNewSection(config, ConfigKeys.RENAME_GROUP.value, self.path.rename_group)        
        config = self.createNewSection(config, ConfigKeys.KEYWORDS.value, self.path.keywords)        
        config = self.createNewSection(config, ConfigKeys.REGEX_RENAME.value, self.path.regex_rename)        
        config = self.createNewSection(config, ConfigKeys.REMOVE_PATTERNS.value, self.path.remove_patterns)        
        config = self.createNewSection(config, ConfigKeys.SETTINGS.value, self.path.settings)        
        
        if 'default_path' not in config[ConfigKeys.DEFAULT.value]:
            config[ConfigKeys.DEFAULT.value]['default_path'] = self.env.DOWNLOAD_COMPLETED_PATH
            with open(self.config_file, 'w') as configfile:
                config.write(configfile)

        return config

    def createNewSection(self, config, SECTION, VALUE):
        if not config.has_section(SECTION):
            config.add_section(SECTION)
            config[SECTION] = VALUE
            with open(self.config_file, "w") as config_file:
                config.write(config_file)
        return config

    def save_config(self):
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
                return True

            return True if os.path.exists(self.config_file) else False
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
            return False

    def edit_key(self, section, key, new_value):
        if section in self.config and key in self.config[section]:
            self.config[section][key] = new_value
            self.save_config()
            return f"Valor de la clave {key} en la sección {section} actualizado a {new_value}."
        else:
            raise ValueError(f"Clave {key} no encontrada en la sección {section}.")

    def add_key(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][str(key)] = value
        self.save_config()
        return value
        return f"Clave {key} añadida a la sección {section} con el valor {value}."

    def delete_key(self, section, key):
        if section in self.config and str(key) in self.config[section]:
            del self.config[section][str(key)]
            self.save_config()
            return True
        else:
            return False

    def get_value(self, section, key):
        self.config.read(self.config_file)
        return self.config[section].get(str(key), None)

    def get_values(self, section, key):
        if section in self.config:
            keywords = {key: value for key, value in self.config.items(section) if key not in self.config.defaults()}
            return keywords
        else:
            return None
        return None











        




