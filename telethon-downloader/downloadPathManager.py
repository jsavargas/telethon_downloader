from env import Env
from info_handler import InfoMessages
from logger_config import logger
from command_controller import CommandController
from config_handler import ConfigKeys, ConfigHandler

import os
import re

class DownloadPathManager:
    def __init__(self):
        self.env = Env()
        self.info_handler = InfoMessages()
        self.command_controller = CommandController()
        self.config_handler = ConfigHandler()

    def charsToReplace(self, filename):
        pattern = '[' + re.escape(self.command_controller.get_chars_to_replace()) + ']'
        return re.sub(pattern, '', filename)
    
    def removePatterns(self, origin_group, filename):
        pattern = self.command_controller.getRemovePatterns(origin_group)
        exists = str(origin_group) in pattern
        if exists:
            file_name = filename.replace(pattern[str(origin_group)],"")
        else:
            for value in pattern:
                if value.startswith("pattern"):
                    auxfilename = filename.replace(pattern[value],"")
                    filename = auxfilename
        return re.sub(r'\s+(?=\.[^.]+$)', '', filename)

    def _getFileRename(self, message, group_id, file_name):
        #logger.info(f"[!] get_file_rename message   : {message}")
        logger.info(f"[!] get_file_rename group_id   : {group_id}")
        logger.info(f"[!] get_file_rename file_name   : {file_name}")

        if not self.config_handler.get_value(ConfigKeys.RENAME_GROUP.value, group_id):
            return file_name

        if not message.caption:
            return file_name

        ext = file_name.split('.')[-1]
        caption = message.caption
        logger.info(f"[!] get_file_rename caption   : {caption}")
        return f"{caption}.{ext}"


    def getDownloadPath(self, message, origin_group, file_name):
        #origin_group = self.info_handler.get_originGroup_test(message)
        if not file_name:
            file_name = self.info_handler.getFileName(message)

        extension = file_name.split('.')[-1]
        textName = file_name # message.caption if message.caption else file_name
        
        if extension == 'torrent': return self.env.DOWNLOAD_PATH_TORRENTS

        file_name = self.clearFilename(message, origin_group, textName)

        logger.info(f"[!] getDownloadPath:: file_name [{file_name}]")
        logger.info(f"[!] getDownloadPath:: textName [{textName}]")
        logger.info(f"[!] getDownloadPath:: origin_group [{origin_group}]")
        logger.info(f"[!] getDownloadPath:: extension [{extension}]")

        if (path := self.getKeywordPath(textName)): return file_name,path
        if (path := self.getGroupPath(origin_group)): return file_name,path
        if (path := self.getExtensionPath(extension)): return file_name,path
        if (path := self.getRegexPath(textName)): return file_name,path
        if (path := self.default_path()): return file_name,path
    
    def getKeywordPath(self, textName):
        keys = self.config_handler.get_values(ConfigKeys.KEYWORDS.value, textName)
        for key in keys:
            if key.lower() in textName.lower():
                return keys[key]
        return None

    def getGroupPath(self, key):
        return self.config_handler.get_value(ConfigKeys.GROUP_PATH.value, key)
    
    def getExtensionPath(self, key):
        return self.config_handler.get_value(ConfigKeys.EXTENSIONS.value, key)

    def getRegexPath(self, filename):
        keys = self.config_handler.get_values(ConfigKeys.REGEX_PATH.value, filename)
        for key in keys:
            match = re.match(r"/(.+?)/(.+?)?$", key)
            if match:
                pattern = match.group(1)   
                flags = re.IGNORECASE if match.group(2) and re.search(r"i", match.group(2),flags=re.IGNORECASE) else 0
                if re.search(pattern, filename, flags=flags):
                    return keys[key]
        return None

    def default_path(self, key="default_path"):
        logger.info(f"[!] default_path")
        return self.config_handler.get_value(ConfigKeys.DEFAULT.value, "default_path")

    def clearFilename(self, message, origin_group, file_name):
        filename = self.charsToReplace(file_name)
        file_name = self.removePatterns(origin_group, filename)
        return re.sub(r'\s+(?=\.[^.]+$)', '', file_name)

    def getDownloadFilename(self, message, origin_group, file_name):

        if not origin_group: origin_group = self.info_handler.get_originGroup_test(message)
        if not file_name: file_name = self.info_handler.getFileName(message)

        logger.info(f"[!] getDownloadFilename origin_group   : {origin_group}")
        logger.info(f"[!] getDownloadFilename file_name   : {file_name}")

        filename = self.charsToReplace(file_name)
        file_name = self.removePatterns(origin_group, filename)

        return re.sub(r'\s+(?=\.[^.]+$)', '', file_name)


if __name__ == "__main__":
    
    download_path_manager = DownloadPathManager()
    
    from types import SimpleNamespace

    message = SimpleNamespace(caption="Este es un caption dinámico")

    getDownloadPath = download_path_manager.getDownloadPath(message, -1001234577, "nombre de tanganna [tof_archivo [tif_ .flac")
    print(f"getDownloadPath: {getDownloadPath}\n")
    
    getDownloadPath = download_path_manager.getDownloadPath(message, -1001234577, "nombre de example [tof_archivo [tif_ .lac")
    print(f"getDownloadPath: {getDownloadPath}\n")
    
    getDownloadPath = download_path_manager.getDownloadPath(message, -1001234577, "nombre de Example [tof_archivo [tif_ .lac")
    print(f"getDownloadPath: {getDownloadPath}\n")
    
    

