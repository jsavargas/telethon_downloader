
from pyrogram import Client, filters, __version__ as pyrogram_version
from pyrogram.types import Message
from pyrogram import enums

from env import Env
from command_controller import CommandController
from command_help import CommandHelp
from logger_config import logger

class CommandHandler:
    def __init__(self, config):
        self.env = Env()
        self.command_controller = CommandController()

        self.command_dict = {
            "ehelp": self.ehandle_help,
            "start": self.handle_help,
            "help": self.handle_help,
            "pyrogram": self.handle_pyrogram_version,
            "ytdlp": self.handle_ytdlp_version,
            "version": self.handle_version,
            "id": self.handle_id,
            "rename": self.rename_file,
            "move": self.rename_file,
            "addextensionpath": self.addExtensionPath,
            "delextensionpath": self.delExtensionPath,
            "addgrouppath": self.addGroupPath,
            "delgrouppath": self.delGroupPath,
            "addkeywordpath": self.addKeywordPath,
            "delkeywordpath": self.delKeywordPath,
            "addrenamegroup": self.addRenameGroup,
            "delrenamegroup": self.addRenameGroup,
        }

        self.command_keys = list(self.command_dict.keys())
        self.bot_version = config.BOT_VERSION
        self.yt_dlp_version = config.YT_DLP_VERSION
        self.pyrogram_version = pyrogram_version


    async def process_command(self, client: Client, message: Message):
        try:

            command = message.command[0]

            user_id = message.from_user.id if message.from_user else None
            if not str(user_id) in self.env.AUTHORIZED_USER_ID and not command == 'id':
                return False

            logger.info(f"process_command:: {command}")
            handler_method = self.command_dict.get(command)

            if self._function_accepts_args(handler_method):
                return await handler_method(client, message)
            else:
                return await handler_method()

        except Exception as e:
            logger.error(f"process_command => Exception: {e}")

    def _function_accepts_args(self, func):
        # Verificar si la función acepta argumentos adicionales
        return hasattr(func, "__code__") and func.__code__.co_argcount > 1

    async def ehandle_help(self, client: Client, message: Message):

        help_text = CommandHelp.get_ehelp()
        
        while help_text:
            # Toma un fragmento de texto de hasta 4096 caracteres.
            chunk = help_text[:4096]
            if len(help_text) > 4096:
                # Encuentra el último espacio para no cortar palabras.
                split_index = chunk.rfind(" ")
                if split_index == -1:  # Si no hay espacios, corta en el límite.
                    split_index = 4096
                chunk = help_text[:split_index]
                help_text = help_text[split_index:].strip()
            else:
                help_text = ""  # Última parte.

            # Envía el fragmento.
            await client.send_message(message.chat.id, chunk)
        
        #await message.reply_text(help_text, parse_mode=enums.ParseMode.DISABLED)

    async def handle_help(self, client: Client, message: Message):


        help_text = CommandHelp.get_help()

        await message.reply_text(help_text, parse_mode=enums.ParseMode.DISABLED)

    async def handle_id(self, client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        await message.reply_text(f"id: {str(user_id)}")

    async def handle_version(self, client: Client, message: Message):
        await message.reply_text(f"version: {str(self.bot_version)}")

    async def handle_pyrogram_version(self, client: Client, message: Message):
        await message.reply_text(f"pyrogram version: {self.pyrogram_version}")

    async def handle_ytdlp_version(self, client: Client, message: Message):
        await message.reply_text(f"ytdlp version: {self.yt_dlp_version}")

    ########## ------------------------------------------------------------------------------------


    def getTempFilename(self, client: Client, message: Message):
        return self.command_controller.getTempFilename(client, message)
    
    async def rename_file(self, client: Client, message: Message):
        await self.command_controller.renameFiles(client, message)

    async def addExtensionPath(self, client: Client, message: Message):
        await self.command_controller.addExtensionPath(client, message)

    async def delExtensionPath(self, client: Client, message: Message):
        await self.command_controller.delExtensionPath(client, message)

    async def addGroupPath(self, client: Client, message: Message):
        await self.command_controller.addGroupPath(client, message)

    async def delGroupPath(self, client: Client, message: Message):
        await self.command_controller.delGroupPath(client, message)

    async def addKeywordPath(self, client: Client, message: Message):
        await self.command_controller.addKeywordPath(client, message)

    async def delKeywordPath(self, client: Client, message: Message):
        await self.command_controller.delKeywordPath(client, message)

    async def addRenameGroup(self, client: Client, message: Message):
        await self.command_controller.addRenameGroup(client, message)

    async def delRenameGroup(self, client: Client, message: Message):
        await self.command_controller.delRenameGroup(client, message)

