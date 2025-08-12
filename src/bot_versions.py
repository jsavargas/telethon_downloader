import yt_dlp

class BotVersions:
    def __init__(self, bot_version, telethon_version, logger):
        self.logger = logger
        try:
            self.bot_version = bot_version
            self.telethon_version = telethon_version
            self.yt_dlp_version = yt_dlp.version.__version__
        except Exception as e:
            self.logger.error(f"Error initializing BotVersions: {e}")
