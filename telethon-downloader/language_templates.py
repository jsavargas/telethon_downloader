# language_templates.py

import os
import shutil
import filecmp


class LanguageTemplates:
    def __init__(self, language="en_US"):
        self.language = language
        self.templates = self.load_templates()

    def initialize_templates(self):
        locale_dir = os.path.join("/config", "locale")

        if not os.path.exists(locale_dir):
            os.makedirs(locale_dir)

        # Rutas de los archivos de plantillas
        en_template_path_original = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "locale", "en_EN.txt"
        )
        es_template_path_original = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "locale", "es_ES.txt"
        )

        en_template_path_target = os.path.join(locale_dir, "en_EN.txt")
        es_template_path_target = os.path.join(locale_dir, "es_ES.txt")

        en_template_exists = os.path.isfile(
            en_template_path_target
        ) and not filecmp.cmp(en_template_path_original, en_template_path_target)
        es_template_exists = os.path.isfile(
            es_template_path_target
        ) and not filecmp.cmp(es_template_path_original, es_template_path_target)

        if en_template_exists or not os.path.exists(en_template_path_target):
            shutil.copy2(en_template_path_original, en_template_path_target)

        if es_template_exists or not os.path.exists(es_template_path_target):
            shutil.copy2(es_template_path_original, es_template_path_target)

        template_file_path = os.path.join(locale_dir, f"{self.language}.txt")

        if os.path.exists(en_template_path_target) and not os.path.exists(
            template_file_path
        ):
            shutil.copy2(en_template_path_original, template_file_path)

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
