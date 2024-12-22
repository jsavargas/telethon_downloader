from telethon.utils import get_peer_id, resolve_id
import telethon
import logger


class CommandHandler:
    def __init__(self, environments):
        self.command_dict = {
            "/help": self.handle_help,
            "/version": self.handle_version,
            "/telethon": self.handle_telethon_version,
            "/id": self.handle_id,
        }

        self.environments = environments

    def process_command(self, message):
        try:
            command = str(message.message)
            logger.logger.info(f"process_command => command: {command}")

            handler_method = self.command_dict.get(command)

            if self._function_accepts_args(handler_method):
                return handler_method(message)
            else:
                return handler_method()

        except Exception as e:
            logger.logger.info(f"process_command => Exception: {e}")

    def _function_accepts_args(self, func):
        # Verificar si la función acepta argumentos adicionales
        return hasattr(func, "__code__") and func.__code__.co_argcount > 1

    def handle_help(self):
        help_message = "Welcome to the bot!\n\n"
        help_message += "Available commands:\n\n"
        help_message += "/id - Shows the user/group ID\n"
        help_message += "/help - Displays the help message\n"
        help_message += "/rename - Change file name by replying or selecting the file and typing the new name\n"
        help_message += "/telethon - Displays the Telethon version\n"
        help_message += "/version - Displays the bot version"
        return help_message

    def handle_version(self):
        logger.logger.info(f"handle_version: {self.environments.VERSION}")
        return f"version: {self.environments.VERSION}"

    def handle_telethon_version(self):
        logger.logger.info(f"handle_telethon_version: {telethon.__version__}")
        return f"telethon version: {telethon.__version__}"

    def handle_id(self, message):
        real_id = get_peer_id(message.peer_id)
        logger.logger.info(f"commands => real_id: {real_id}")
        return f"id: {str(real_id)}"
