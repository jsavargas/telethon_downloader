import logger

import os
import asyncio

class FileExtractor:
    def __init__(self):
        self.data = []

    async def descomprimir_unrar(self, archivo, directorio_destino):
        comando = f'unrar x "{archivo}" -o "{directorio_destino}"'
        logger.logger.info(f'descomprimir_unrar => comando: {comando}')

        process = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

    async def descomprimir_unzip(self, archivo, directorio_destino):
        comando = f'unzip -o "{archivo}" -d "{directorio_destino}"'
        process = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

    async def descomprimir_7z(self, archivo, directorio_destino):
        comando = f'7z x "{archivo}" -o"{directorio_destino}"'
        process = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
