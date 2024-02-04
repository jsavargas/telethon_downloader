import re
import os

import logger
import configparser


class DownloadPathManager:
    def __init__(self, SECTIONS):
        self.SECTIONS = SECTIONS

    def getREGEXPATH(self, filename):
        download_path = None
        try:
            for REGEX_PATH in self.SECTIONS["REGEX_PATH"]:
                logger.logger.info(
                    f"getREGEXPATH :::: filename=[{filename}] REGEX_PATH=[{REGEX_PATH}]"
                )
                flags = 0
                pattern = REGEX_PATH
                if re.search(r"/i$", REGEX_PATH):
                    pattern = REGEX_PATH[:-2]
                    flags = re.IGNORECASE
                pattern = pattern.strip("/")
                logger.logger.info(
                    f"pattern i :::: filename=[{filename}] pattern=[{pattern}] flags=[{flags}] "
                )
                if re.search(pattern, filename, flags=flags):
                    download_path = os.path.join(
                        self.SECTIONS["REGEX_PATH"][REGEX_PATH]
                    )
                    return download_path
                    break
            logger.logger.info(f"getREGEXPATH download_path: {download_path}")
        except Exception as e:
            logger.logger.error(f"getREGEXPATH Exception: {e}")

        return download_path
