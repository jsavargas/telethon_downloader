import configparser


class ConfigurationManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        config = configparser.ConfigParser()
        config.optionxform = str

        DEFAULT_PATH = {
            "pdf": "/download/pdf",
            "cbr": "/download/pdf",
            "mp3": "/download/mp3",
            "flac": "/download/mp3",
            "jpg": "/download/jpg",
            "mp4": "/download/mp4",
        }

        if not config.read(self.config_path):
            # Config file doesn't exist, create a new one with default values
            config["DEFAULT"] = {"pdf": "/download/pdf", "cbr": "/download/pdf"}
            config["DEFAULT_PATH"] = DEFAULT_PATH
            config["REGEX_PATH"] = {"/example/i": "/download/example"}

            config["GROUP_PATH"] = {"0000000000": "/download/example"}

            with open(self.config_path, "w") as config_file:
                config.write(config_file)

        if not config.has_section("DEFAULT_PATH"):
            config.add_section("DEFAULT_PATH")
            config["DEFAULT_PATH"] = DEFAULT_PATH
            with open(self.config_path, "w") as config_file:
                config.write(config_file)

        if not config.has_section("GROUP_PATH"):
            config.add_section("GROUP_PATH")
            config.set("GROUP_PATH", "0000000000", "/download/example")
            with open(self.config_path, "w") as config_file:
                config.write(config_file)

        if not config.has_section("REGEX_PATH"):
            config.add_section("REGEX_PATH")
            config.set("REGEX_PATH", "/example/i", "/download/example")
            with open(self.config_path, "w") as config_file:
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

    def get_all_sections(self):
        all_data = {}
        for section in self.config.sections():
            all_data[section] = dict(self.config.items(section))
        return all_data
