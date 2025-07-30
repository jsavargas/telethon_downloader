import os
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
from urllib.parse import quote, unquote

class KeyboardManager:
    def __init__(self, logger, base_download_path):
        self.logger = logger
        self.base_download_path = base_download_path

    async def send_directory_browser(self, message_id, current_dir, page=0, summary_text=""):
        all_items = os.listdir(current_dir)
        self.logger.info(f"Items in {current_dir}: {all_items}")
        dirs = [d for d in all_items if os.path.isdir(os.path.join(current_dir, d))]
        self.logger.info(f"Directories in {current_dir}: {dirs}")
        dirs.sort()

        items_per_page = 4
        total_pages = (len(dirs) + items_per_page - 1) // items_per_page
        
        start_index = page * items_per_page
        end_index = start_index + items_per_page
        current_page_dirs = dirs[start_index:end_index]

        buttons = []
        for i in range(0, len(current_page_dirs), 2):
            row = []
            row.append(KeyboardButtonCallback(current_page_dirs[i], data=f"dir_{message_id}_{quote(current_page_dirs[i])}_{page}".encode('utf-8')))
            if i + 1 < len(current_page_dirs):
                row.append(KeyboardButtonCallback(current_page_dirs[i+1], data=f"dir_{message_id}_{quote(current_page_dirs[i+1])}_{page}".encode('utf-8')))
            buttons.append(row)

        nav_buttons = []
        if current_dir != self.base_download_path:
            nav_buttons.append(KeyboardButtonCallback("Up", data=f"nav_{message_id}_up_{quote(os.path.dirname(current_dir))}_{page}".encode('utf-8')))
        if page > 0:
            nav_buttons.append(KeyboardButtonCallback("Back", data=f"nav_{message_id}_back_{quote(current_dir)}_{page}".encode('utf-8')))
        nav_buttons.append(KeyboardButtonCallback("This", data=f"nav_{message_id}_this_{quote(current_dir)}_{page}".encode('utf-8')))
        if page < total_pages - 1:
            nav_buttons.append(KeyboardButtonCallback("Next", data=f"nav_{message_id}_next_{quote(current_dir)}_{page}".encode('utf-8')))
        buttons.append(nav_buttons)

        buttons.append([KeyboardButtonCallback("New Folder", data=f"new_{message_id}".encode('utf-8'))])
        buttons.append([KeyboardButtonCallback("Cancel", data=f"cancel_{message_id}".encode('utf-8'))])

        browser_text = f"""Current Directory: {current_dir}
Page: {page + 1}/{total_pages if total_pages > 0 else 1}"""
        
        if summary_text:
            text = f"{summary_text}\n\n{browser_text}"
        else:
            text = browser_text
            
        return text, buttons

    def get_download_buttons(self, message_id):
        buttons = [
            [KeyboardButtonCallback("Move", data=f"move_{message_id}".encode('utf-8'))],
            [KeyboardButtonCallback("Ok", data=f"ok_{message_id}".encode('utf-8'))]
        ]
        return ReplyInlineMarkup(buttons)

    def get_cancel_button(self, message_id):
        buttons = [[KeyboardButtonCallback("Cancel", data=f"cancel_{message_id}".encode('utf-8'))]]
        return ReplyInlineMarkup(buttons)

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