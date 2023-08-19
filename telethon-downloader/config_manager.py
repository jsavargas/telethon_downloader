import configparser

class ConfigurationManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        config = configparser.ConfigParser()

        if not config.read(self.config_path):
            # Config file doesn't exist, create a new one with default values
            config['DEFAULT'] = {'key1': 'value1', 'key2': 'value2'}
            config['DEFAULT_PATH'] = {
                'pdf': '/download/pdf',
                'cbr': '/download/pdf',
                'mp3': '/download/mp3',
                'flac': '/download/mp3',
                'jpg': '/download/jpg',
                'mp4': '/download/mp4',            
            }
            config['REGEX_PATH'] = {'/example/i': '/download/example'}
            
            with open(self.config_path, 'w') as config_file:
                config.write(config_file)

        return config

    def get_value(self, section, key):
        return self.config.get(section, key)
    
    def get_section_keys(self, section_name):
        if section_name in self.config:
            section = self.config[section_name]
            return section.keys()
        else:
            return []
