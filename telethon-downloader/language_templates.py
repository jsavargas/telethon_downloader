# language_templates.py

import os


class LanguageTemplates:
    def __init__(self, language="en_US"):
        self.language = language
        self.templates = self.load_templates()

    def initialize_templates(self):
        en_templates = [
            "WELCOME=Telethon Downloader Started: Version: {msg1}",
            "PROGRESS_CALLBACK_PATH=Download in {path}",
            "PROGRESS_CALLBACK_PROGRESS=progress: {current:.2f} MB / {total:.2f} MB",
            "",
            "MESSAGE_DOWNLOAD=Downloading in: {path}",
            "",
            "MESSAGE_DOWNLOAD_FILE=File downloaded in: {downloaded_file}",
            "MESSAGE_DOWNLOAD_FILE_SIZE=File size: {file_size:.2f} MB",
            "MESSAGE_DOWNLOAD_COMPLETED=Download completed in: {elapsed_time}",
            "MESSAGE_DOWNLOAD_SPEED=Average download speed: {speed:.2f} MB/s",
            "MESSAGE_DOWNLOAD_AT=at: {end_time}",
            "MESSAGE_DOWNLOAD_FROM_ID=from: {from_id}",
            "",
            "MESSAGE_TIMEOUT_EXCEEDED=Download timeout exceeded...",
            "MESSAGE_EXCEPTION=Download exception...",
            "MESSAGE_NO_LINKS_DOWNLOAD=No links to download.",
            "",
            "HOUR=hour",
            "MINUTE=minute",
            "SECOND=second",
            "",
            "HOURS=hours",
            "MINUTES=minutes",
            "SECONDS=seconds",
        ]

        es_templates = [
            "WELCOME=Telethon Downloader Iniciado: Version: {msg1}",
            "PROGRESS_CALLBACK_PATH=Descarga en {path}",
            "PROGRESS_CALLBACK_PROGRESS=progreso: {current:.2f} MB / {total:.2f} MB",
            "",
            "MESSAGE_DOWNLOAD=Descargando en: {path}",
            "",
            "MESSAGE_DOWNLOAD_FILE=Archivo descargado en: {downloaded_file}",
            "MESSAGE_DOWNLOAD_FILE_SIZE=Tamaño del archivo: {file_size:.2f} MB",
            "MESSAGE_DOWNLOAD_COMPLETED=Descarga completada en: {elapsed_time}",
            "MESSAGE_DOWNLOAD_SPEED=Velocidad de descarga promedio: {speed:.2f} MB/s",
            "MESSAGE_DOWNLOAD_AT=a las: {end_time}",
            "MESSAGE_DOWNLOAD_FROM_ID=desde: {from_id}",
            "",
            "MESSAGE_TIMEOUT_EXCEEDED=Excedido el tiempo de espera de la descarga...",
            "MESSAGE_EXCEPTION=Excepción durante la descarga...",
            "MESSAGE_NO_LINKS_DOWNLOAD=No hay enlaces para descargar.",
            "",
            "HOUR=hora",
            "MINUTE=minuto",
            "SECOND=segundo",
            "",
            "HOURS=horas",
            "MINUTES=minutos",
            "SECONDS=segundos",
        ]

        locale_dir = os.path.join("/config", "locale")
        en_template_path = os.path.join(locale_dir, "en_EN.txt")
        es_template_path = os.path.join(locale_dir, "es_ES.txt")

        if not os.path.exists(locale_dir):
            os.makedirs(locale_dir)

        with open(en_template_path, "w", encoding="utf-8") as en_template_file:
            en_template_file.write("\n".join(en_templates) + "\n")

        with open(es_template_path, "w", encoding="utf-8") as es_template_file:
            es_template_file.write("\n".join(es_templates) + "\n")

        template_file_path = os.path.join(locale_dir, f"{self.language}.txt")

        if not os.path.exists(template_file_path):
            with open(template_file_path, "w", encoding="utf-8") as template_file_path:
                template_file_path.write("\n".join(en_templates) + "\n")

    def load_templates(self):
        locale_dir = os.path.join("/config", "locale")
        template_file_path = os.path.join(locale_dir, f"{self.language}.txt")

        self.initialize_templates()

        try:
            with open(template_file_path, "r", encoding="utf-8") as template_file:
                template_lines = template_file.read().strip().split("\n")
                templates = {}
                for line in template_lines:
                    parts = line.split("=")
                    if len(parts) == 2:
                        templates[parts[0]] = parts[1]
                return templates
        except FileNotFoundError:
            return {}

    def template(self, template_name, default_message="Language template not found."):
        return self.templates.get(template_name, default_message) + os.linesep

    def templateOneLine(
        self, template_name, default_message="Language template not found."
    ):
        return self.templates.get(template_name, default_message)
