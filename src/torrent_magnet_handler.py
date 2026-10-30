import time
from telethon.tl.types import KeyboardButtonCallback
from urllib.parse import quote


class TorrentMagnetHandler:
    def __init__(self, bot, env_config, download_manager, downloaded_files, finalize_callback, logger):
        self.bot = bot
        self.env_config = env_config
        self.download_manager = download_manager
        self.downloaded_files = downloaded_files
        self._finalize_download_processing = finalize_callback
        self.logger = logger

    async def handle_magnet_link(self, event):
        if self.env_config.TORRENT_MODE.lower() == 'watch':
            return
        self.logger.info(f"Magnet link detected in message ID: {event.message.id}")
        magnet_uri = event.message.text
        initial_message = await event.reply("Magnet link received. Choosing category...")

        self.downloaded_files[initial_message.id] = {
            'original_message_id': event.message.id,
            'source_type': 'magnet',
            'source_data': magnet_uri,
            'file_info': magnet_uri,
            'download_type': 'magnet',
            'user_id': event.sender_id,
            'initial_message_id': initial_message.id,
            'initial_message_chat_id': initial_message.chat_id
        }
        await self.ask_for_category(initial_message)

    async def handle_new_category_name(self, event):
        try:
            target_message_id = None
            for msg_id, file_info in self.downloaded_files.items():
                if file_info.get('waiting_for_category_name', False):
                    target_message_id = msg_id
                    break

            if target_message_id is None:
                return

            new_category_name = event.message.text
            download_info = self.downloaded_files[target_message_id]
            source_type = download_info.get('source_type', 'file')
            source_data = download_info.get('downloaded_file_path') or download_info.get('source_data')
            destination_path = download_info.get('final_destination_dir') if source_type == 'file' else None

            final_file_path = None
            if source_type == 'file':
                final_file_path = self.download_manager.move_to_completed(source_data, destination_path, category=new_category_name)
            elif source_type == 'magnet':
                final_file_path = self.download_manager.add_magnet_link_with_category(source_data, new_category_name)

            if final_file_path:
                original_message = await self.bot.get_messages(download_info['user_id'], ids=download_info['original_message_id'])
                initial_message = await self.bot.get_messages(download_info['initial_message_chat_id'], ids=download_info['initial_message_id'])

                await self.bot.edit_message(initial_message.chat_id, initial_message.id, "Processing torrent...", buttons=None)
                start_time = download_info.get('start_time', time.time()) if source_type == 'file' else time.time()
                await self._finalize_download_processing(
                    initial_message, original_message,
                    download_info['file_info'],
                    destination_path,
                    start_time,
                    time.time(),
                    download_info.get('file_size', 0) if source_type == 'file' else 0,
                    download_info.get('origin_group') if source_type == 'file' else None,
                    download_info['user_id'],
                    download_info.get('channel_id') if source_type == 'file' else None,
                    download_info.get('file_extension', 'torrent') if source_type == 'file' else 'torrent',
                    final_file_path,
                    download_type=download_info.get('download_type', 'file')
                )
                await event.delete()
            else:
                await self.bot.edit_message(
                    download_info['initial_message_chat_id'],
                    download_info['initial_message_id'],
                    "Failed to add torrent.", buttons=None
                )

            del self.downloaded_files[target_message_id]
        except Exception as e:
            self.logger.error(f"Error handling new category name: {e}")
            await event.reply(f"Error creating new category: {e}")

    async def ask_for_category(self, initial_message):
        categories = self.download_manager.torrent_manager.get_categories()
        buttons = []
        for category in categories:
            buttons.append([KeyboardButtonCallback(category, data=f"category_{initial_message.id}_{quote(category)}")])
        buttons.append([KeyboardButtonCallback("Add New Category", data=f"category_{initial_message.id}_new")])
        buttons.append([KeyboardButtonCallback("No Category", data=f"category_{initial_message.id}_none")])
        await self.bot.edit_message(initial_message.chat_id, initial_message.id, "Choose a category for the torrent:", buttons=buttons)
