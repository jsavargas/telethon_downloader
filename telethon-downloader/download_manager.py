import re
import os

import logger
import configparser


class DownloadPathManager:
    def __init__(self, SECTIONS):
        self.SECTIONS = SECTIONS

    def getREGEXPATH(self, filename):
        logger.logger.info(f"getREGEXPATH :::: filename=[{filename}]")
        download_path = None
        try:
            for REGEX_PATH in self.SECTIONS["REGEX_PATH"]:
                flags = 0
                pattern = REGEX_PATH
                if re.search(r"/i$", REGEX_PATH):
                    pattern = REGEX_PATH[:-2]
                    flags = re.IGNORECASE
                pattern = pattern.strip("/")
                if re.search(pattern, filename, flags=flags):
                    download_path = os.path.join(
                        self.SECTIONS["REGEX_PATH"][REGEX_PATH]
                    )
                    return download_path
        except Exception as e:
            logger.logger.error(f"getREGEXPATH Exception: {e}")

        return download_path
