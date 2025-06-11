from logger_config import logger
from env import Env
from config_handler import ConfigKeys, ConfigHandler
from data_handler import FileDataHandler
from utils import Utils
from info_handler import InfoMessages

import os
import shutil


class CommandController:
    def __init__(self):
        self.env = Env()
        self.config_handler = ConfigHandler()
        self.data_handler = FileDataHandler()
        self.utils = Utils()
        self.info_handler = InfoMessages()
        self.tempFilename = {}

    def is_reply(self, message):
        return message.reply_to_message is not None

    def getDefaultPath(self):
        return self.config_handler.get_value(ConfigKeys.DEFAULT.value, "default_path")

    def getDefaultPathExtension(self, extension):
        switch = {
            'torrent': self.env.DOWNLOAD_PATH_TORRENTS
        }
        return switch.get(extension, None)

    async def renameFiles(self, client, message):        
        try:
            command = message.command[0]
            if self.is_reply(message):
                file_info = self.data_handler.get_download_file(message.reply_to_message_id)
                logger.info(f"rename_file file_info      : {file_info}")
             
                if file_info and len(message.command) > 1:
                    new_name = ' '.join(message.command[1:])
                    new_filename = self.utils.combine_paths(file_info, new_name)
                    logger.info(f"rename_file update_download_files : {new_name} => {new_filename}")

                    new_dir = os.path.dirname(new_filename)
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                    dest = shutil.move(file_info, new_filename)  

                    logger.info(f"rename_file os.rename : [{file_info}], [{new_filename}] => [{dest}]")
                    update_download_files = self.data_handler.update_download_files(message.reply_to_message_id, new_filename)
                    logger.info(f"rename_file os.rename update_download_files: [{update_download_files}]")
                    if update_download_files:
                        await message.reply_text(f"File renamed to {dest}")
                    return True

                if file_info and len(message.command) == 1:
                    from downloadPathManager import DownloadPathManager
                    manager = DownloadPathManager()

                    download_path = manager.getDownloadPath(message, None, None)
                    file_name = manager.getDownloadFilename(message.reply_to_message, None, None)
                    new_filename = os.path.join(download_path, file_name)


                    if not os.path.exists(download_path):
                        os.makedirs(download_path)
                    dest = shutil.move(file_info, new_filename)  

                    update_download_files = self.data_handler.update_download_files(message.reply_to_message_id, new_filename)
                    logger.info(f"rename_file os.rename update_download_files: [{update_download_files}]")

                    await message.reply_text(f"File renamed to {dest}")

                    logger.info(f"[!] renameFiles file_info   : {file_info}")
                    logger.info(f"[!] renameFiles download_path   : {download_path}")
                    logger.info(f"[!] renameFiles file_name   : {file_name}")
                    logger.info(f"[!] renameFiles new_filename   : {new_filename}")



                elif file_info is None and len(message.command) > 1:

                    from downloadPathManager import DownloadPathManager
                    manager = DownloadPathManager()

                    filename = ' '.join(message.command[1:])

                    download_path = manager.getDownloadPath(message, None, None)
                    file_name = manager.getDownloadFilename(message.reply_to_message, None, None)

                    logger.info(f"[!] renameFiles download_path   : {download_path}")
                    logger.info(f"[!] renameFiles file_name   : {file_name}")
                    logger.info(f"[!] renameFiles filename   : {filename}")

                    new_filename = filename

                    base_a, ext_a = os.path.splitext(filename)
                    _, ext_b = os.path.splitext(file_name)
                    
                    if not ext_a and ext_b:
                        new_filename = f"{base_a}{ext_b}"

                    origin_group = self.info_handler.get_originGroup_test(message)
                    
                    logger.info(f"[!] renameFiles new_filename   : {new_filename}")
                    logger.info(f"[!] renameFiles id   : {message.reply_to_message_id}")
                    logger.info(f"[!] renameFiles origin_group   : {origin_group}")

                    key = (origin_group, message.reply_to_message_id)

                    # Agregar al diccionario
                    self.tempFilename[key] = {
                        "origin_group": origin_group,
                        "message_id": message.reply_to_message_id,
                        "new_filename": new_filename,
                    }
                    reply = await message.reply_text(f"New file name {new_filename}.")

        except Exception as e:
            logger.error(f"renameFiles Exception [{e}]")
   
    def getTempFilename(self, client, message):
        try:
            origin_group = self.info_handler.get_originGroup_test(message)
            key = (origin_group, message.id)
            
            if key in self.tempFilename:
                logger.info(f"[!] getTempFilename new_filename   : {self.tempFilename[key]['new_filename']}")
                new_filename = self.tempFilename[key]['new_filename']
                del self.tempFilename[key]
                return new_filename
            else: 
                return None
        except Exception as e:
            logger.error(f"getTempFilename Exception [{e}]")

    def getExtensionPath(self, key):
        path = self.getDefaultPathExtension(key)
        return path if path else self.config_handler.get_value(ConfigKeys.EXTENSIONS.value, key) or self.getDefaultPath()

    async def addExtensionPath(self, client, message):
        try:
            if self.is_reply(message):
                ext = self.info_handler.getFileExtension(message.reply_to_message).replace(".", "")
                logger.info(f"addExtensionPath ext: {ext}")
                if ext and len(message.command) == 1:
                    path = os.path.join(self.env.DOWNLOAD_PATH, ext)
                    add_key = self.config_handler.add_key(ConfigKeys.EXTENSIONS.value, ext, path)
                    logger.info(f"addExtensionPath path: {add_key}")
                    await message.reply_text(f"Path for .{ext} added: {path}.")
                if ext and len(message.command) > 1:
                    path = ' '.join(message.command[1:])
                    if not path.startswith('/'):
                        path = os.path.join(self.env.DOWNLOAD_PATH, path)
                    add_key = self.config_handler.add_key(ConfigKeys.EXTENSIONS.value, ext, path)
                    logger.info(f"addExtensionPath path: {add_key}")
                    await message.reply_text(f"Path for .{ext} added: {path}.")
            else:
                if len(message.command) == 2:
                    ext = message.command[1]
                    path = os.path.join(self.env.DOWNLOAD_PATH, ext)
                    add_key = self.config_handler.add_key(ConfigKeys.EXTENSIONS.value, ext, path)
                    logger.info(f"addExtensionPath path: {add_key}")
                    await message.reply_text(f"Path for .{ext} added: {path}.")
                if len(message.command) > 2:
                    ext = message.command[1]
                    path = ' '.join(message.command[2:])
                    if not path.startswith('/'):
                        path = os.path.join(self.env.DOWNLOAD_PATH, path)
                    add_key = self.config_handler.add_key(ConfigKeys.EXTENSIONS.value, ext, path)
                    logger.info(f"addExtensionPath path: {add_key}")
                    await message.reply_text(f"Path for .{ext} added: {path}.")
        except Exception as e:
            logger.error(f"addExtensionPath Exception [{e}]")

    async def delExtensionPath(self, client, message):
        try:
            if self.is_reply(message):
                ext = self.info_handler.getFileExtension(message.reply_to_message).replace(".", "")
                delete_key = self.config_handler.delete_key(ConfigKeys.EXTENSIONS.value, ext)
                logger.info(f"delExtensionPath ext: {ext}")
                logger.info(f"delExtensionPath delete_key: {delete_key}")
                await message.reply_text(f"Extension {ext} removed to EXTENSIONS list.")
            elif len(message.command) > 1:
                ext = message.command[1]
                delete_key = self.config_handler.delete_key(ConfigKeys.EXTENSIONS.value, ext)
                logger.info(f"delExtensionPath ext: {ext}")
                logger.info(f"delExtensionPath delete_key: {delete_key}")
                await message.reply_text(f"Extension {ext} removed to EXTENSIONS list.")
        except Exception as e:
            logger.error(f"delExtensionPath Exception [{e}]")

    def getGroupPath(self, key):
        return self.config_handler.get_value(ConfigKeys.GROUP_PATH.value, key)

    async def addGroupPath(self, client, message):
        try:
            if self.is_reply(message):
                origin_group = self.info_handler.get_originGroup_test(message)
                if origin_group:
                    path = (
                        os.path.join(self.env.DOWNLOAD_PATH, str(origin_group).replace('-', '')) 
                        if len(message.command) == 1 else 
                        ' '.join(message.command[1:])
                    )
                    if not path.startswith('/'):
                        path = os.path.join(self.env.DOWNLOAD_PATH, path)
                    add_key = self.config_handler.add_key(ConfigKeys.GROUP_PATH.value, origin_group, path)
                    logger.info(f"addGroupPath path: {add_key}")
                    await message.reply_text(f"Path for {origin_group} added: {path}.")
            else:
                if 2 <= len(message.command):
                    origin_group = message.command[1]
                    path = (
                        os.path.join(self.env.DOWNLOAD_PATH, ' '.join(message.command[2:]))
                        if len(message.command) > 2 else
                        os.path.join(self.env.DOWNLOAD_PATH, origin_group)
                    )
                    if not path.startswith('/'):
                        path = os.path.join(self.env.DOWNLOAD_PATH, path)
                    add_key = self.config_handler.add_key(ConfigKeys.GROUP_PATH.value, origin_group, path)
                    logger.info(f"addGroupPath path: {add_key}")
                    await message.reply_text(f"Path for {origin_group} added: {path}.")
        except Exception as e:
            logger.error(f"addGroupPath Exception [{e}]")

    async def delGroupPath(self, client, message):
        try:
            origin_group = None
            if self.is_reply(message):
                origin_group = self.info_handler.get_originGroup_test(message)
            elif len(message.command) > 1:
                origin_group = message.command[1]
            if origin_group:
                delete_key = self.config_handler.delete_key(ConfigKeys.GROUP_PATH.value, origin_group)
                logger.info(f"delGroupPath delete_key: {delete_key}")
                await message.reply_text(f"Group {origin_group} removed from GROUP_PATH list.")
        except Exception as e:
            logger.error(f"delGroupPath Exception [{e}]")

    def getKeywordPath(self, key):
        sections = self.config_handler.get_values(ConfigKeys.KEYWORDS.value, key)
        if not key: return None
        for section in sections:
            if section.lower() in key.lower():
                return sections[section]
        return None


    async def addKeywordPath(self, client, message):
        pass

    async def delKeywordPath(self, client, message):
        pass

    async def addRenameGroup(self, client, message):
        pass

    async def delRenameGroup(self, client, message):
        pass



    def getRemovePattern(self, key):
        return self.config_handler.get_value(ConfigKeys.REMOVE_PATTERNS.value, key)

    def getRemovePatterns(self, key):
        return self.config_handler.get_values(ConfigKeys.REMOVE_PATTERNS.value, key)

    def get_chars_to_replace(self):
        return self.config_handler.get_value(ConfigKeys.SETTINGS.value, "chars_to_replace")
