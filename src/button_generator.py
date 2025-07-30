from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
import logging

class ButtonGenerator:
    def __init__(self, logger):
        self.logger = logger

    def get_download_buttons(self, message_id):
        try:
            buttons = [
                [KeyboardButtonCallback("Move", data=f"move_{message_id}".encode('utf-8'))],
                [KeyboardButtonCallback("Ok", data=f"ok_{message_id}".encode('utf-8'))]
            ]
            return ReplyInlineMarkup(buttons)
        except Exception as e:
            self.logger.error(f"Error generating download buttons: {e}")
            return None

    def get_directory_buttons(self, message_id, current_page_dirs, page, current_dir, total_pages):
        try:
            buttons = []
            for i in range(0, len(current_page_dirs), 2):
                row = []
                row.append(KeyboardButtonCallback(current_page_dirs[i], data=f"dir_{message_id}_{current_page_dirs[i]}_{page}".encode('utf-8')))
                if i + 1 < len(current_page_dirs):
                    row.append(KeyboardButtonCallback(current_page_dirs[i+1], data=f"dir_{message_id}_{current_page_dirs[i+1]}_{page}".encode('utf-8')))
                buttons.append(row)

            nav_buttons = []
            if page > 0:
                nav_buttons.append(KeyboardButtonCallback("Back", data=f"nav_{message_id}_back_{current_dir}_{page}".encode('utf-8')))
            nav_buttons.append(KeyboardButtonCallback("This", data=f"nav_{message_id}_this_{current_dir}_{page}".encode('utf-8')))
            if page < total_pages - 1:
                nav_buttons.append(KeyboardButtonCallback("Next", data=f"nav_{message_id}_next_{current_dir}_{page}".encode('utf-8')))
            buttons.append(nav_buttons)

            buttons.append([KeyboardButtonCallback("Cancel", data=f"cancel_{message_id}".encode('utf-8'))])
            return ReplyInlineMarkup(buttons)
        except Exception as e:
            self.logger.error(f"Error generating directory buttons: {e}")
            return None
