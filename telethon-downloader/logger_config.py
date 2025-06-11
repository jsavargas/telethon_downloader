# logger_config.py
import logging
import sys
from io import StringIO

# Crear un buffer de StringIO para capturar solo los logs de nivel ERROR de Pyrogram
pyrogram_log_stream = StringIO()

# Configurar el handler para la consola que muestra INFO y superior
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Mostrar INFO y superior en la consola

# Configurar el handler para el buffer que captura solo ERROR
buffer_handler = logging.StreamHandler(pyrogram_log_stream)
buffer_handler.setLevel(logging.ERROR)  # Solo capturar mensajes de nivel ERROR

# Configurar el formato de los handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
buffer_handler.setFormatter(formatter)

# Configurar el logger principal (logger) si es necesario
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Captura INFO y superior
logger.addHandler(console_handler)

# Configurar el logger de Pyrogram
pyrogram_logger = logging.getLogger("pyrogram")
pyrogram_logger.setLevel(logging.WARNING)  # Captura INFO y superior
pyrogram_logger.addHandler(console_handler)
pyrogram_logger.addHandler(buffer_handler)

# Función para obtener el último mensaje de error de Pyrogram
def get_last_error_log():
    log_contents = pyrogram_log_stream.getvalue().strip().split('\n')
    last_error_log = next((log for log in reversed(log_contents) if "ERROR" in log), None)
    return last_error_log
