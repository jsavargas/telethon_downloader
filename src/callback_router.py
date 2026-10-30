from urllib.parse import unquote
import time


class CallbackRouter:
    def __init__(self, file_download_handler, commands_manager, torrent_magnet_handler, file_browser_handler, pending_downloads_manager, logger):
        self.file_download_handler = file_download_handler
        self.commands_manager = commands_manager
        self.torrent_magnet_handler = torrent_magnet_handler
        self.file_browser_handler = file_browser_handler
        self.pending_downloads_manager = pending_downloads_manager
        self.logger = logger

        self.downloaded_files = file_download_handler.downloaded_files
        self.media_groups = file_download_handler.media_groups

    async def route(self, event):
        try:
            data = event.data.decode('utf-8')
            self.logger.info(f"Callback data received: {data}")

            if await self._try_add_path_callback(event, data):
                return

            parts = data.split('_')

            if parts[0] == 'group':
                await self._handle_group(event, parts)
                return

            if parts[0] == 'category':
                await self._handle_category(event, parts)
                return

            if data.startswith('cancel_download'):
                await self._handle_cancel_download(event, parts)
                return

            if parts[0] == 'resume':
                await self._handle_resume(event, parts)
                return

            await self._handle_file_browser(event, data, parts)

        except Exception as e:
            self.logger.error(f"Unhandled exception in callback router: {e}")
            await event.answer(f"Error processing callback: {e}")

    async def _try_add_path_callback(self, event, data):
        if data == 'add_extension_path':
            await self.commands_manager.start_add_extension_path(event)
            return True
        if data == 'add_group_path':
            await self.commands_manager.start_add_group_path(event)
            return True

        sender_id = event.sender_id
        prompt_info = (
            self.commands_manager.active_add_extension_prompts.get(sender_id) or
            self.commands_manager.active_add_group_prompts.get(sender_id)
        )
        if prompt_info and prompt_info.get('state') == 'waiting_for_path':
            await self._handle_add_path_nav(event, data, sender_id, prompt_info)
            return True
        return False

    async def _handle_add_path_nav(self, event, data, sender_id, prompt_info):
        parts = data.split('_')
        action = parts[0]

        try:
            if action == 'dir':
                selected_dir_name = unquote(parts[2])
                current_base_dir = prompt_info.get('current_dir', self.file_download_handler.env_config.BASE_DOWNLOAD_PATH)
                new_full_path = __import__('os').path.join(current_base_dir, selected_dir_name)
                prompt_info['current_dir'] = new_full_path
                text, buttons = await self.file_browser_handler.keyboard_manager.send_directory_browser(int(parts[1]), new_full_path, page=0)
                await event.edit(text, buttons=buttons)
            elif action == 'nav':
                nav_action = parts[2]
                current_dir = prompt_info.get('current_dir', self.file_download_handler.env_config.BASE_DOWNLOAD_PATH)
                page = int(parts[4])
                os = __import__('os')
                if nav_action == 'next':
                    page += 1
                elif nav_action == 'back':
                    page -= 1
                elif nav_action == 'up':
                    current_dir = os.path.dirname(current_dir)
                    page = 0
                prompt_info['current_dir'] = current_dir
                if nav_action == 'this':
                    path = current_dir
                    if sender_id in self.commands_manager.active_add_extension_prompts:
                        self.commands_manager.config_manager.add_extension_path(prompt_info['extension'], path)
                        await event.edit(f"Path for `.{prompt_info['extension']}` set to `{path}`.", buttons=None)
                        del self.commands_manager.active_add_extension_prompts[sender_id]
                    elif sender_id in self.commands_manager.active_add_group_prompts:
                        self.commands_manager.config_manager.add_group_path(prompt_info['group_id'], path)
                        await event.edit(f"Path for group '{prompt_info['group_id']}' set to `{path}`.", buttons=None)
                        del self.commands_manager.active_add_group_prompts[sender_id]
                    return
                text, buttons = await self.file_browser_handler.keyboard_manager.send_directory_browser(int(parts[1]), current_dir, page)
                await event.edit(text, buttons=buttons)
            elif action == 'new':
                prompt_info['state'] = 'waiting_for_new_folder_name'
                prompt_info['browser_message_id'] = int(parts[1])
                await event.edit("Please send the name for the new folder.")
            elif action == 'cancel':
                if sender_id in self.commands_manager.active_add_extension_prompts:
                    del self.commands_manager.active_add_extension_prompts[sender_id]
                elif sender_id in self.commands_manager.active_add_group_prompts:
                    del self.commands_manager.active_add_group_prompts[sender_id]
                await event.edit("Operation cancelled.", buttons=None)
        except (IndexError, ValueError, KeyError) as e:
            self.logger.error(f"Error handling add path callback '{data}': {e}")
            await event.answer("Invalid or expired action.")

    async def _handle_group(self, event, parts):
        try:
            action_type = '_'.join(parts[1:-1])
            user_facing_group_id = int(parts[-1])
            if user_facing_group_id not in self.media_groups:
                await event.answer("Group information not found.")
                return
            group_info = self.media_groups[user_facing_group_id]
            if action_type == 'move_all':
                await self.file_browser_handler.handle_group_move_all(event, user_facing_group_id, group_info)
            elif action_type == 'ok':
                await self.file_browser_handler.handle_group_ok(event, user_facing_group_id, group_info)
        except (IndexError, ValueError) as e:
            self.logger.error(f"Error handling group callback: {e}")
            await event.answer("Invalid or expired action.")

    async def _handle_category(self, event, parts):
        try:
            message_id = int(parts[1])
            category = unquote(parts[2]) if len(parts) > 2 else None

            if message_id not in self.downloaded_files:
                await event.answer("Original download information not found.")
                return

            download_info = self.downloaded_files[message_id]
            source_type = download_info.get('source_type', 'file')

            if category == 'new':
                self.downloaded_files[message_id]['waiting_for_category_name'] = True
                await self.file_download_handler.bot.edit_message(event.chat_id, message_id, "Please send the name for the new category.", buttons=None)
                return

            if source_type == 'file':
                torrent_path = download_info['downloaded_file_path']
                destination_path = download_info['final_destination_dir']
                final_file_path = self.file_download_handler.download_manager.move_to_completed(torrent_path, destination_path, category=category if category != 'none' else None)
            elif source_type == 'magnet':
                magnet_uri = download_info['source_data']
                destination_path = None
                final_file_path = self.file_download_handler.download_manager.add_magnet_link_with_category(magnet_uri, category if category != 'none' else None)
            else:
                final_file_path = None

            if final_file_path:
                initial_message = await self.file_download_handler.bot.get_messages(download_info['initial_message_chat_id'], ids=download_info['initial_message_id'])
                original_message = await self.file_download_handler.bot.get_messages(download_info['user_id'], ids=download_info['original_message_id'])
                await self.file_download_handler.bot.edit_message(initial_message.chat_id, initial_message.id, "Processing torrent...", buttons=None)
                await self.file_download_handler._finalize_download_processing(
                    initial_message, original_message,
                    download_info['file_info'], destination_path,
                    download_info.get('start_time', time.time()), time.time(),
                    download_info.get('file_size', 0),
                    download_info.get('origin_group'),
                    download_info['user_id'],
                    download_info.get('channel_id'),
                    download_info.get('file_extension', 'torrent'),
                    final_file_path,
                    download_type=download_info.get('download_type', 'file')
                )
            else:
                await self.file_download_handler.bot.edit_message(event.chat_id, message_id, "Failed to add torrent.", buttons=None)
            del self.downloaded_files[message_id]
        except (IndexError, ValueError, KeyError) as e:
            self.logger.error(f"Error handling category callback: {e}")
            await event.answer("Invalid or expired action.")

    async def _handle_cancel_download(self, event, parts):
        try:
            message_id = int(parts[2])
            await event.edit("Download cancelled.", buttons=None)
            if not self.file_download_handler.cancel_download(message_id):
                await event.answer("Could not find download to cancel.")
        except (IndexError, ValueError) as e:
            self.logger.error(f"Error handling cancel_download callback: {e}")
            await event.answer("Invalid or expired action.")

    async def _handle_resume(self, event, parts):
        try:
            action = '_'.join(parts[:2])
            if action == 'resume_one':
                message_id = int(parts[2])
                await self.pending_downloads_manager.resume_one(message_id, event)
            elif action == 'resume_all':
                await self.pending_downloads_manager.resume_all(event)
            elif action == 'resume_cancel':
                await self.pending_downloads_manager.cancel(event)
        except (IndexError, ValueError) as e:
            self.logger.error(f"Error handling resume callback: {e}")
            await event.answer("Invalid or expired action.")

    async def _handle_file_browser(self, event, data, parts):
        try:
            message_id = int(parts[1])
            action = parts[0]

            if action == 'move':
                if message_id in self.downloaded_files:
                    file_info = self.downloaded_files[message_id]
                    self.downloaded_files[message_id]['browser_chat_id'] = event.chat_id
                    self.downloaded_files[message_id]['browser_message_id'] = event.message_id
                    text, buttons = await self.file_browser_handler.keyboard_manager.send_directory_browser(message_id, file_info['current_dir'], summary_text=file_info.get('summary_text', ""))
                    await event.edit(text, buttons=buttons)
            elif action in ('ok', 'cancel'):
                if message_id in self.downloaded_files:
                    summary_text = self.downloaded_files[message_id].get('summary_text', "Download operation ok.")
                    del self.downloaded_files[message_id]
                    await event.edit(summary_text, buttons=None)
                else:
                    await event.answer("File information not found.")
            elif action == 'new':
                if message_id in self.downloaded_files:
                    self.downloaded_files[message_id]['waiting_for_folder_name'] = True
                    self.downloaded_files[message_id]['browser_message_id'] = event.message_id
                    summary_text = self.downloaded_files[message_id].get('summary_text', "")
                    await event.edit(f"{summary_text}\n\nPlease send the name for the new folder.")
                else:
                    await event.answer("File information not found.")
            elif action == 'dir':
                selected_dir_name = unquote(parts[2])
                page = int(parts[3])
                if message_id in self.downloaded_files:
                    current_base_dir = self.downloaded_files[message_id]['current_dir']
                    new_full_path = __import__('os').path.join(current_base_dir, selected_dir_name)
                    self.downloaded_files[message_id]['current_dir'] = new_full_path
                    text, buttons = await self.file_browser_handler.keyboard_manager.send_directory_browser(message_id, new_full_path, page=0)
                    await event.edit(text, buttons=buttons)
            elif action == 'nav':
                nav_action = parts[2]
                page = int(parts[4])
                if message_id in self.downloaded_files:
                    os = __import__('os')
                    current_dir = self.downloaded_files[message_id]['current_dir']
                    if nav_action == 'next':
                        page += 1
                    elif nav_action == 'back':
                        page -= 1
                    elif nav_action == 'up':
                        current_dir = os.path.dirname(current_dir)
                        page = 0
                    self.downloaded_files[message_id]['current_dir'] = current_dir
                    if nav_action == 'this':
                        self.downloaded_files[message_id]['browser_chat_id'] = event.chat_id
                        self.downloaded_files[message_id]['browser_message_id'] = event.message_id
                        await self.file_browser_handler.handle_nav_this(event, message_id, current_dir)
                        return
                    text, buttons = await self.file_browser_handler.keyboard_manager.send_directory_browser(message_id, current_dir, page)
                    await event.edit(text, buttons=buttons)
                else:
                    await event.answer("File information not found.")

            await event.answer()
        except (IndexError, ValueError, KeyError) as e:
            self.logger.error(f"Error handling file browser callback '{data}': {e}")
            await event.answer("Invalid or expired action.")
