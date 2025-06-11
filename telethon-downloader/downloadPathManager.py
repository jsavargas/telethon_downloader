from env import Env
from info_handler import InfoMessages
from logger_config import logger
from command_controller import CommandController

import os
import re

class DownloadPathManager:
    def __init__(self):
        self.env = Env()
        self.info_handler = InfoMessages()
        self.command_controller = CommandController()

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
        origin_group = self.info_handler.get_originGroup_test(message)
        if not file_name:
            file_name = self.info_handler.getFileName(message)

        extension = file_name.split('.')[-1]
        textName = message.caption if message.caption else file_name
        
        if extension == 'torrent': return self.env.DOWNLOAD_PATH_TORRENTS

        returnPathDownload = (
            self.command_controller.getKeywordPath(textName) or
            self.command_controller.getGroupPath(origin_group) or
            self.command_controller.getExtensionPath(extension)
        )

        logger.info(f"[!] getDownloadPath:: [{returnPathDownload}]")
        return returnPathDownload
    
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
    
    
    
    getDownloadFilename = download_path_manager.getDownloadFilename("", -1001234577, "nombre de [tof_archivo [tif_ .ext")


    print(f"getDownloadFilename: {getDownloadFilename}")