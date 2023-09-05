# language_templates.py

import os

class LanguageTemplates:
    def __init__(self, language="en_US"):
        self.language = language
        self.templates = self.load_templates()

    def load_templates(self):
        locale_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
        template_file_path = os.path.join(locale_dir, f'{self.language}.txt')
        
        try:
            with open(template_file_path, 'r', encoding='utf-8') as template_file:
                template_lines = template_file.read().strip().split('\n')
                templates = {}
                for line in template_lines:
                    parts = line.split('=')
                    if len(parts) == 2:
                        templates[parts[0]] = parts[1]
                return templates
        except FileNotFoundError:
            return {}

    def template(self, template_name, default_message="Language template not found."):
        return self.templates.get(template_name, default_message) + os.linesep 

    def templateOneLine(self, template_name, default_message="Language template not found."):
        return self.templates.get(template_name, default_message)

