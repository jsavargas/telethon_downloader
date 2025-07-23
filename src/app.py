
from pyrogram import Client, filters
from pyrogram.types import Message
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Replace with your actual API ID and API HASH
# Get them from my.telegram.org
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

AUTHORIZED_USER_ID = os.environ.get("AUTHORIZED_USER_ID")

if not API_ID or not API_HASH or not BOT_TOKEN or not AUTHORIZED_USER_ID:
    logger.error("Please set the environment variables API_ID, API_HASH, BOT_TOKEN, and AUTHORIZED_USER_ID.")
    exit(1)

AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in AUTHORIZED_USER_ID.split(',')]


app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.on_message(filters.document & filters.user(AUTHORIZED_USER_IDS))
async def download_document(client: Client, message: Message):
    if message.document:
        file_name = message.document.file_name
        await message.reply_text(f"Downloading {file_name}...")
        try:
            file_path = await client.download_media(message, file_name=os.path.join(DOWNLOAD_DIR, file_name))
            await message.reply_text(f"Downloaded {file_name} to {file_path}")
        except Exception as e:
            logger.error(f"Error downloading {file_name}: {e}")
            await message.reply_text(f"Error downloading {file_name}: {e}")

@app.on_message(filters.command("start") & filters.private & filters.user(AUTHORIZED_USER_IDS))
async def start_command(client: Client, message: Message):
    await message.reply_text("Hello! Send me a document and I will download it.")

async def main():
    await app.start()
    logger.info("Bot started.")
    try:
        await app.send_message(AUTHORIZED_USER_IDS[0], "Bot has started!")
    except Exception as e:
        logger.error(f"Error sending start message to authorized user: {e}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
