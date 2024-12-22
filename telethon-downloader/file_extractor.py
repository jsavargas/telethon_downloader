import os
import asyncio
import logger


class FileExtractor:
    def __init__(self):
        self.data = []

    async def extract_unrar(self, file, destination_directory):
        try:
            command = f'unrar x "{file}" -o "{destination_directory}"'
            logger.logger.info(f"extract_unrar starting => command: {command}")

            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            logger.logger.info(f"extract_unrar finish => command: {command}")
        except Exception as e:
            logger.logger.error(f"Error extracting with unrar: {str(e)}")

    async def extract_unzip(self, file, destination_directory):
        try:
            command = f'unzip -o "{file}" -d "{destination_directory}"'
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            logger.logger.error(f"Error extracting with unzip: {str(e)}")

    async def extract_7z(self, file, destination_directory):
        try:
            command = f'7z x "{file}" -o"{destination_directory}"'
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            logger.logger.error(f"Error extracting with 7z: {str(e)}")
