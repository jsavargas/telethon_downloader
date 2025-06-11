# variable_printer.py
from env import Env
from logger_config import logger  # Importar el logger configurado

class PartialPrinter:
    def __init__(self, constants=[]):
        self.env = Env()

    def print_variable(self, variable_name, variable_value):
        """Prints the variable name and its value in the desired format."""
        logger.info(f"{variable_name:<30}: {variable_value}")

    def print_partial_value(self, variable_name, variable_value):
        try:
            """Prints the variable name and half of its value, padded with asterisks."""
            if isinstance(variable_value, list):
                masked_list = []
                for item in variable_value:
                    if isinstance(item, str):
                        half_len = len(item) // 2
                        masked_value = item[:half_len] + "*" * (len(item) - half_len)
                    elif isinstance(item, (int, float)):
                        str_item = str(item)
                        half_len = len(str_item) // 2
                        masked_value = str_item[:half_len] + "*" * (len(str_item) - half_len)
                    else:
                        masked_value = item  # Mantener el valor original si no es str, int, o float
                    masked_list.append(masked_value)
                masked_value_str = str(masked_list)
                logger.info(f"{variable_name:<30}: {masked_value_str}")

            elif isinstance(variable_value, str):
                half_len = len(variable_value) // 2
                masked_value = variable_value[:half_len] + "*" * (len(variable_value) - half_len)
                logger.info(f"{variable_name:<30}: {masked_value}")
            elif isinstance(variable_value, (int, float)):
                masked_value = str(variable_value)[:int(len(str(variable_value)) / 2)] + "*" * (
                    len(str(variable_value)) - int(len(str(variable_value)) / 2)
                )
                logger.info(f"{variable_name:<30}: {masked_value}")
            else:
                logger.info(f"{variable_name:<30}: {variable_value}")
                #raise TypeError(f"Unsupported type for variable_value: {type(variable_value)}")
        except Exception as e:
            logger.error(f"print_variable Exception: {variable_value}: {e}")

    def print_variables(self):
        self.print_partial_value("API_ID", self.env.API_ID)
        self.print_partial_value("API_HASH", self.env.API_HASH)
        self.print_partial_value("BOT_TOKEN", self.env.BOT_TOKEN)
        self.print_partial_value("AUTHORIZED_USER_ID", self.env.AUTHORIZED_USER_ID)
        self.print_variable("DOWNLOAD_DIR", self.env.DOWNLOAD_PATH)
        self.print_variable("DOWNLOAD_INCOMPLETED_PATH", self.env.DOWNLOAD_INCOMPLETED_PATH)
        self.print_variable("DOWNLOAD_COMPLETED_PATH", self.env.DOWNLOAD_COMPLETED_PATH)
        self.print_variable("DOWNLOAD_PATH_TORRENTS", self.env.DOWNLOAD_PATH_TORRENTS)
        self.print_variable("PROGRESS_DOWNLOAD", self.env.PROGRESS_DOWNLOAD)
        self.print_variable("PROGRESS_STATUS_SHOW", self.env.PROGRESS_STATUS_SHOW)
        self.print_variable("MAX_CONCURRENT_TASKS", self.env.MAX_CONCURRENT_TASKS)
        self.print_variable("WORKERS", self.env.WORKERS)
        self.print_variable("MAX_CONCURRENT_TRANSMISSIONS", self.env.MAX_CONCURRENT_TRANSMISSIONS)
