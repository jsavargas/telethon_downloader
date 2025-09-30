import logging
import os
from telethon.tl.types import Message, ReplyInlineMarkup, KeyboardButtonCallback

class Commands:
    def __init__(self, bot_version, welcome_message_generator, download_tracker, download_manager, bot, keyboard_manager, config_manager, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.bot_version = bot_version
        self.welcome_message_generator = welcome_message_generator
        self.download_tracker = download_tracker
        self.download_manager = download_manager
        self.bot = bot
        self.keyboard_manager = keyboard_manager
        self.config_manager = config_manager
        self.active_rename_prompts = {}
        self.active_add_extension_prompts = {}
        self.active_add_group_prompts = {}
        self.command_dict = {
            "/version": self.version,
            "/start": self.start,
            "/rename": self.rename,
            "/addpath": self.addpath,
            "/help": self.help,
        }
        self.command_descriptions = {
            "/version": "Shows the bot version.",
            "/start": "Shows the welcome message.",
            "/rename": "Renames a downloaded file. Reply to a file message with /rename <new_name>.",
            "/addpath": "Shows the menu to add new paths for extensions or groups.",
            "/help": "Shows this help message.",
        }

    async def help(self, event):
        help_text = self._get_help_text()
        await event.reply(help_text)

    def _get_help_text(self):
        help_text = "Available commands:\n\n"
        for command, description in self.command_descriptions.items():
            help_text += f"{command}: {description}\n"
        
        help_text += "\n"
        help_text += "GitHub: https://github.com/jsavargas/telegram-downloader\n"
        help_text += "Docker Hub: https://hub.docker.com/r/jsavargas/telethon_downloader\n"
        return help_text

    async def addpath(self, event):
        buttons = self.keyboard_manager.get_addpath_buttons()
        await event.reply("Please choose an option:", buttons=buttons)

    async def start_add_group_path(self, event):
        sender_id = event.sender_id
        self.active_add_group_prompts[sender_id] = {'state': 'waiting_for_group_id'}
        await event.edit("Please send the group id", buttons=None)

    async def start_add_extension_path(self, event):
        sender_id = event.sender_id
        self.active_add_extension_prompts[sender_id] = {'state': 'waiting_for_extension'}
        await event.edit("Please send the extension (e.g., pdf, jpg).", buttons=None)

    async def handle_extension_input(self, event):
        sender_id = event.sender_id
        if sender_id not in self.active_add_extension_prompts or self.active_add_extension_prompts[sender_id]['state'] != 'waiting_for_extension':
            return

        extension = event.text.strip().lower()
        self.active_add_extension_prompts[sender_id]['extension'] = extension
        self.active_add_extension_prompts[sender_id]['state'] = 'waiting_for_path'

        # Now show the directory browser
        temp_message = await event.reply("Loading directory browser...")
        text, buttons = await self.keyboard_manager.send_directory_browser(temp_message.id, self.download_manager.base_download_path)
        await temp_message.edit(text, buttons=buttons)

    async def handle_group_id_input(self, event):
        sender_id = event.sender_id
        if sender_id not in self.active_add_group_prompts or self.active_add_group_prompts[sender_id]['state'] != 'waiting_for_group_id':
            return

        group_id = event.text.strip()
        self.active_add_group_prompts[sender_id]['group_id'] = group_id
        self.active_add_group_prompts[sender_id]['state'] = 'waiting_for_path'

        # Show directory browser
        temp_message = await event.reply("Loading directory browser...")
        text, buttons = await self.keyboard_manager.send_directory_browser(temp_message.id, self.download_manager.base_download_path)
        await temp_message.edit(text, buttons=buttons)

    async def _perform_rename_operation(self, original_file_path, new_name_input, message_id, prompt_message):
        try:
            # Determine the new full path
            if os.path.isabs(new_name_input): # If input is an absolute path
                new_full_path = new_name_input
            else: # If input is just a new name, assume same directory and preserve extension
                file_extension = os.path.splitext(original_file_path)[1]
                new_full_path = os.path.join(os.path.dirname(original_file_path), new_name_input + file_extension)
            
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)

            # Move and rename the file
            os.rename(original_file_path, new_full_path)
            self.download_manager._apply_permissions_and_ownership(new_full_path)

            # Update the download tracker
            self.download_tracker.update_status(
                message_id,
                'completed',
                final_filename=new_full_path,
                download_type='file' # Assuming rename only for file downloads
            )

            await prompt_message.edit(f"File successfully renamed/moved from '{os.path.basename(original_file_path)}' to '{os.path.basename(new_full_path)}'.", buttons=None)
            # await event.delete() # Delete the user's message with the new name - this is handled by the caller

        except FileNotFoundError:
            await prompt_message.edit(f"Error: Original file not found at {original_file_path}.", buttons=None)
        except OSError as e:
            await prompt_message.edit(f"Error renaming/moving file: {e}", buttons=None)
            self.logger.error(f"Error renaming/moving file {original_file_path} to {new_full_path}: {e}")
        except Exception as e:
            self.logger.error(f"Unhandled error during rename: {e}")
            await prompt_message.edit(f"An unexpected error occurred during rename: {e}", buttons=None)

    async def version(self, event):
        version_message = f"Bot Version: {self.bot_version}"
        await event.reply(version_message)

    async def start(self, event):
        welcome_message = self.welcome_message_generator.get_message()
        help_text = self._get_help_text()
        combined_message = f"{welcome_message}\n\n{help_text}"
        await event.reply(combined_message)

    async def rename(self, event):
        if not event.message.is_reply:
            await event.reply("Please reply to the file's download message or the file itself with /rename.")
            return

        replied_message_id = event.message.reply_to_msg_id
        download_info = self.download_tracker.get_download_by_message_id(replied_message_id)

        if not download_info:
            await event.reply("Could not find download information for the replied message. Make sure it's a message from a file download.")
            return

        current_file_path = download_info.get('current_file_path')
        if not current_file_path or not os.path.exists(current_file_path):
            await event.reply(f"File not found at the recorded path: {current_file_path}. Cannot rename.")
            return

        args = event.message.text.split(' ', 1)
        if len(args) > 1: # New name provided directly in the command
            new_name_input = args[1].strip()
            prompt_message = await event.reply(f"Renaming '{os.path.basename(current_file_path)}' to '{new_name_input}'...")
            await self._perform_rename_operation(current_file_path, new_name_input, replied_message_id, prompt_message)
            await event.delete() # Delete the user's command message
        else: # No new name provided, prompt for it
            self.active_rename_prompts[event.sender_id] = {
                'message_id': replied_message_id,
                'original_file_path': current_file_path,
                'prompt_message': await event.reply(f"Please send the new name or full path for '{os.path.basename(current_file_path)}'.")
            }

    async def handle_new_rename_input(self, event):
        sender_id = event.sender_id
        if sender_id not in self.active_rename_prompts:
            return # Not an active rename prompt

        rename_info = self.active_rename_prompts.pop(sender_id) # Remove prompt after receiving input
        original_file_path = rename_info['original_file_path']
        prompt_message = rename_info['prompt_message']
        new_name_input = event.message.text.strip()

        await self._perform_rename_operation(original_file_path, new_name_input, rename_info['message_id'], prompt_message)
        await event.delete() # Delete the user's message with the new name

    def register_command(self, command_name, handler_function):
        if not command_name.startswith('/'):
            command_name = '/' + command_name
        self.command_dict[command_name] = handler_function
        self.logger.info(f"Command '{command_name}' registered.")

    async def execute_command(self, command_name, *args, **kwargs):
        handler = self.command_dict.get(command_name)
        if handler:
            self.logger.info(f"Executing command '{command_name}'.")
            return await handler(*args, **kwargs)
        else:
            self.logger.warning(f"Command '{command_name}' not found.")
            return None