import asyncio

class PendingDownloadsManager:
    def __init__(self, download_tracker, logger, telethon_bot):
        self.download_tracker = download_tracker
        self.logger = logger
        self.telethon_bot = telethon_bot

    async def resume_one(self, message_id, event):
        self.logger.info(f"Resuming download for message ID: {message_id}")
        download_info = self.download_tracker.get_download_by_message_id(message_id)
        if download_info:
            message = await event.get_message()
            current_buttons = message.buttons
            new_buttons = []
            clicked_button_data = f"resume_one_{message_id}".encode('utf-8')

            for row in current_buttons:
                new_row = [button for button in row if button.data != clicked_button_data]
                if new_row:
                    new_buttons.append(new_row)

            if len(new_buttons) <= 1:
                await event.edit("All pending downloads are being processed.", buttons=None)
            else:
                await event.edit(message.text, buttons=new_buttons)

            asyncio.create_task(self.telethon_bot.process_download(download_info['message_id'], download_info['user_id'], download_info['download_type']))
        else:
            self.logger.warning(f"Could not find download info for message ID: {message_id}")

    async def resume_all(self, event):
        self.logger.info("Resuming all pending downloads.")
        pending_downloads = self.download_tracker.get_pending_downloads()
        self.logger.info(f"Found {len(pending_downloads)} pending downloads to resume.")
        for download in pending_downloads:
            self.logger.info(f"Resuming download: {download}")
            asyncio.create_task(self.telethon_bot.process_download(download['message_id'], download['user_id'], download['download_type']))
        await event.edit("Resuming all pending downloads.", buttons=None)

    async def cancel(self, event):
        self.logger.info("Canceling resume operation.")
        self.download_tracker.clear_pending_downloads()
        await event.edit("Download resume operation canceled.", buttons=None)
