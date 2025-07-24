import os
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
from urllib.parse import quote, unquote

class KeyboardManager:
    def __init__(self, logger, base_download_path):
        self.logger = logger
        self.base_download_path = base_download_path

    async def send_directory_browser(self, message_id, current_dir, page=0):
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

        text = f"""Current Directory: {current_dir}
Page: {page + 1}/{total_pages if total_pages > 0 else 1}"""
        return text, buttons