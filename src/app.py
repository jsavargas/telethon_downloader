from telethon import TelegramClient, events
import os
import asyncio
from logger_config import LoggerConfig

class TelethonDownloaderBot:
    def __init__(self):
        self.logger = LoggerConfig(__name__).get_logger()

        self.API_ID = os.environ.get("API_ID")
        self.API_HASH = os.environ.get("API_HASH")
        self.BOT_TOKEN = os.environ.get("BOT_TOKEN")
        self.AUTHORIZED_USER_ID = os.environ.get("AUTHORIZED_USER_ID")

        if not self.API_ID or not self.API_HASH or not self.BOT_TOKEN or not self.AUTHORIZED_USER_ID:
            self.logger.error("Please set the environment variables API_ID, API_HASH, BOT_TOKEN, and AUTHORIZED_USER_ID.")
            exit(1)

        self.AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in self.AUTHORIZED_USER_ID.split(',')]

        self.bot = TelegramClient('bot', self.API_ID, self.API_HASH)

        self.DOWNLOAD_DIR = "downloads"
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        self._add_handlers()

    def _add_handlers(self):
        @self.bot.on(events.NewMessage(incoming=True, func=lambda e: (e.message.document or e.message.photo) and e.sender_id in self.AUTHORIZED_USER_IDS))
        async def download_media(event):
            message = event.message
            file_info = "media"
            if message.document:
                file_info = message.document.attributes[0].file_name if message.document.attributes else 'unknown_document'
            elif message.photo:
                file_info = f"photo_{message.id}.jpg" # Telethon will generate a name, but we can use this for display

            initial_message = await message.reply(f"Downloading {file_info}...")
            try:
                file_path = await self.bot.download_media(message, file=self.DOWNLOAD_DIR)
                await initial_message.edit(f"Downloaded {file_info} to {file_path}")
            except Exception as e:
                self.logger.error(f"Error downloading {file_info}: {e}")
                await initial_message.edit(f"Error downloading {file_info}: {e}")

        @self.bot.on(events.NewMessage(pattern='/start', incoming=True, func=lambda e: e.sender_id in self.AUTHORIZED_USER_IDS))
        async def start_command(event):
            await event.reply("Hello! Send me a document and I will download it.")

    async def run(self):
        await self.bot.start(bot_token=self.BOT_TOKEN)
        self.logger.info("Bot started.")
        try:
            await self.bot.send_message(self.AUTHORIZED_USER_IDS[0], "Bot has started!")
        except Exception as e:
            self.logger.error(f"Error sending start message to authorized user: {e}")
        await self.bot.run_until_disconnected()

if __name__ == "__main__":
    bot_instance = TelethonDownloaderBot()
    asyncio.run(bot_instance.run())
