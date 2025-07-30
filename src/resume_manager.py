from telethon.tl.types import KeyboardButtonCallback

class ResumeManager:
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger

    async def ask_to_resume(self, pending_downloads, user_id):
        if not pending_downloads:
            self.logger.info("No pending downloads found.")
            return

        self.logger.info(f"Found {len(pending_downloads)} pending downloads. Asking user to resume.")

        message_text = "Found pending downloads. What would you like to do?"
        buttons = []

        for download in pending_downloads:
            filename = download.get('filename', f"Unknown File (ID: {download['message_id']})")
            buttons.append([KeyboardButtonCallback(f"Resume {filename}", data=f"resume_one_{download['message_id']}")])

        buttons.append([KeyboardButtonCallback("Resume All", data="resume_all"), KeyboardButtonCallback("Cancel", data="resume_cancel")])

        try:
            await self.bot.send_message(user_id, message_text, buttons=buttons)
        except Exception as e:
            self.logger.error(f"Failed to send resume message to user {user_id}: {e}")
