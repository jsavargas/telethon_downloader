from telethon.utils import get_peer_id, resolve_id

import logger
import constants

class CommandHandler:
    def __init__(self, environments):
        self.commands = {
            '/help': self.show_help,
            '/version': self.show_version
        }
        self.environments = environments
    
    async def handle_command(self, command, event):
        handler = self.commands.get(command)
        if handler:
            await handler(event)
    
    async def show_help(self, message):
        help_message = "¡Bienvenido al bot!\n\n"
        help_message += "Comandos disponibles:\n"
        help_message += "/help - Muestra la ayuda\n"
        help_message += "/version - Muestra la versión del programa"
        await message.respond(help_message)
    
    async def show_version(self, event):
        await event.respond(f'version: {self.environments.VERSION}')

    async def show_id(self, message):
        real_id = get_peer_id(message.peer_id)
        logger.logger.info(f'commands => real_id: {real_id}')
        await message.respond(f'id: {str(real_id)}')
