import os
from telethon.tl.types import KeyboardButtonCallback


class FileBrowserHandler:
    def __init__(self, bot, keyboard_manager, download_manager, download_tracker, env_config, downloaded_files, media_groups, logger):
        self.bot = bot
        self.keyboard_manager = keyboard_manager
        self.download_manager = download_manager
        self.download_tracker = download_tracker
        self.env_config = env_config
        self.downloaded_files = downloaded_files
        self.media_groups = media_groups
        self.logger = logger

    async def handle_new_folder_name(self, event):
        try:
            target_message_id = None
            for msg_id, file_info in self.downloaded_files.items():
                if file_info.get('waiting_for_folder_name', False):
                    target_message_id = msg_id
                    break

            if not target_message_id:
                return

            file_info = self.downloaded_files[target_message_id]
            is_group_move = file_info.get('is_group', False)
            new_folder_name = event.message.text
            current_dir = file_info['current_dir']
            new_folder_path = os.path.join(current_dir, new_folder_name)
            browser_message_id = file_info.get('browser_message_id')
            browser_chat_id = file_info.get('browser_chat_id')

            os.makedirs(new_folder_path, exist_ok=True)
            self.download_manager._apply_permissions_and_ownership(new_folder_path)
            file_info['waiting_for_folder_name'] = False

            if is_group_move:
                internal_group_id = file_info['internal_group_id']
                group_info = self.media_groups[internal_group_id]
                moved_files_count = 0
                moved_files_list = []
                for msg_id, f_info in group_info['files'].items():
                    if f_info['status'] == 'completed' and f_info['path']:
                        new_path = self.download_manager.move_file(f_info['path'], new_folder_path)
                        if new_path:
                            moved_files_count += 1
                            moved_files_list.append(f_info['filename'])
                            self.download_tracker.update_status(msg_id, 'completed', final_filename=new_path, download_type='file')
                files_str = "\n".join(moved_files_list)
                summary_text = f"Created folder **{new_folder_name}** and moved {moved_files_count}/{group_info['total_files']} files to it:\n{files_str}"
                await self.bot.edit_message(browser_chat_id, browser_message_id, summary_text, buttons=None)
                del self.downloaded_files[target_message_id]
                del self.media_groups[internal_group_id]
            else:
                file_path = file_info['file_path']
                new_file_path = self.download_manager.move_file(file_path, new_folder_path)
                if new_file_path:
                    self.download_tracker.update_status(target_message_id, 'completed', final_filename=new_file_path, download_type=file_info.get('download_type', 'file'))
                    summary_text = file_info.get('summary_text', "")
                    await self.bot.edit_message(browser_chat_id, browser_message_id, f"{summary_text}\n\nFolder '{new_folder_name}' created and file moved successfully to {new_file_path}", buttons=None)
                    del self.downloaded_files[target_message_id]
                else:
                    await event.reply(f"Folder '{new_folder_name}' created, but there was an error moving the file.")

        except Exception as e:
            self.logger.error(f"Error creating new folder: {e}")
            await event.reply(f"Error creating folder: {e}")

    async def handle_media_group_completion(self, grouped_id, chat_id):
        group_info = self.media_groups.get(grouped_id)
        if not group_info:
            return
        user_facing_group_id = group_info['user_facing_group_id']
        summary_text = f"All {group_info['total_files']} files in the media group have been downloaded.\n\nWhat would you like to do with them?"
        buttons = [
            [KeyboardButtonCallback("Move All to New Folder", data=f"group_move_all_{user_facing_group_id}")],
            [KeyboardButtonCallback("Ok Group Operation", data=f"group_ok_{user_facing_group_id}")]
        ]
        await self.bot.send_message(chat_id, summary_text, buttons=buttons)

    async def handle_group_move_all(self, event, internal_grouped_id, group_info):
        initial_message_id = group_info['initial_message_id']
        for file_msg_id, f_info in group_info['files'].items():
            try:
                msg = await self.bot.get_messages(event.chat_id, ids=f_info['initial_message_id'])
                if msg:
                    await msg.edit(msg.text, buttons=None)
            except Exception as e:
                self.logger.error(f"Could not remove buttons from message {f_info.get('initial_message_id')}: {e}")

        self.downloaded_files[initial_message_id] = {
            'is_group': True,
            'internal_group_id': internal_grouped_id,
            'current_dir': self.env_config.BASE_DOWNLOAD_PATH,
            'summary_text': f"Moving {group_info['total_files']} files.",
            'browser_chat_id': event.chat_id,
            'browser_message_id': event.message_id
        }
        summary_text = f"Moving {group_info['total_files']} files."
        text, buttons = await self.keyboard_manager.send_directory_browser(initial_message_id, self.env_config.BASE_DOWNLOAD_PATH, summary_text=summary_text)
        await event.edit(text, buttons=buttons)

    async def handle_group_ok(self, event, internal_grouped_id, group_info):
        for file_msg_id, f_info in group_info['files'].items():
            try:
                msg = await self.bot.get_messages(event.chat_id, ids=f_info['initial_message_id'])
                if msg:
                    await msg.edit(msg.text, buttons=None)
            except Exception as e:
                self.logger.error(f"Could not remove buttons from message {f_info.get('initial_message_id')}: {e}")
        await event.delete()
        del self.media_groups[internal_grouped_id]

    async def handle_nav_this(self, event, message_id, destination_dir):
        file_info = self.downloaded_files[message_id]
        summary_text = file_info.get('summary_text', "")
        is_group_move = file_info.get('is_group', False)

        if is_group_move:
            internal_group_id = file_info['internal_group_id']
            group_info = self.media_groups[internal_group_id]
            moved_count = 0
            moved_list = []
            for msg_id, f_info in group_info['files'].items():
                if f_info.get('status') == 'completed' and f_info.get('path'):
                    new_path = self.download_manager.move_file(f_info['path'], destination_dir)
                    if new_path:
                        moved_count += 1
                        moved_list.append(f_info['filename'])
                        self.download_tracker.update_status(msg_id, 'completed', final_filename=new_path, download_type='file')
            files_str = "\n".join(moved_list)
            final_summary = f"Moved {moved_count}/{group_info['total_files']} files to **{destination_dir}**:\n{files_str}"
            await event.edit(final_summary, buttons=None)
            del self.downloaded_files[message_id]
            del self.media_groups[internal_group_id]
        else:
            file_path = file_info['file_path']
            new_file_path = self.download_manager.move_file(file_path, destination_dir)
            if new_file_path:
                self.download_tracker.update_status(message_id, 'completed', final_filename=new_file_path, download_type=file_info.get('download_type', 'file'))
                await event.edit(f"{summary_text}\n\nFile moved successfully to {new_file_path}", buttons=None)
                del self.downloaded_files[message_id]
            else:
                await event.edit(f"{summary_text}\n\nError moving file.", buttons=None)
