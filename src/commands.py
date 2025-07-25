import logging

class Commands:
    def __init__(self, bot_version, welcome_message_generator, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.bot_version = bot_version
        self.welcome_message_generator = welcome_message_generator
        self.command_dict = {
            "/version": self.version,
            "/start": self.start,
        }

    async def version(self, event):
        version_message = f"Bot Version: {self.bot_version}"
        await event.reply(version_message)

    async def start(self, event):
        version_message = self.welcome_message_generator.get_message()
        await event.reply(version_message)

    def register_command(self, command_name, handler_function):
        if not command_name.startswith('/'):
            command_name = '/' + command_name
        self.command_dict[command_name] = handler_function
        self.logger.info(f"Command '{command_name}' registered.")

    async def execute_command(self, command_name, *args, **kwargs):
        handler = self.command_dict.get(command_name)
        if handler:
            self.logger.info(f"Executing command '{command_name}'.")
            return await handler(*args, **kwargs)
        else:
            self.logger.warning(f"Command '{command_name}' not found.")
            return None