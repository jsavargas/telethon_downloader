import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
from logger_config import logger
from user_state_manager import UserStateManager

class FolderNavigator:
    def __init__(self):
        self.base_path = os.path.abspath("/download")
        self.user_states = {}  # user_id -> {"path": str, "page": int, "on_select": function}
        self.user_state_manager = UserStateManager()

    def list_folders(self, path):
        try:
            entries = os.listdir(path)
            return sorted([f for f in entries if os.path.isdir(os.path.join(path, f))])

            folders = [
                os.path.abspath(os.path.join(self.base_path, entry))
                for entry in os.listdir(self.base_path)
                if os.path.isdir(os.path.join(self.base_path, entry))
            ]
            return folders
        except Exception:
            return []

    def build_keyboard(self, user_id):
        #state = self.user_states[user_id]
        state = self.user_state_manager.get(user_id)
        logger.info(f"build_keyboard state: {state}")

        path = state["path"]
        page = state["page"]
        folders = self.list_folders(path)

        per_page = 6
        total_pages = (len(folders) + per_page - 1) // per_page
        page = max(0, min(page, total_pages - 1))
        state["page"] = page

        start = page * per_page
        end = start + per_page
        current_folders = folders[start:end]

        keyboard = []

        for folder in current_folders:
            keyboard.append([
                InlineKeyboardButton(f"📁 {os.path.basename(os.path.normpath(folder))}", callback_data=f"folder:{folder}")
            ])

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⏪ Previous", callback_data="prev"))
        if os.path.abspath(path) != "/":
            nav_buttons.append(InlineKeyboardButton("⏫ Up", callback_data="up"))
        if end < len(folders):
            nav_buttons.append(InlineKeyboardButton("⏩ Next", callback_data="next"))
        if nav_buttons:
            keyboard.append(nav_buttons)

        # Final action row
        keyboard.append([
            InlineKeyboardButton("📂 This Directory", callback_data="select"),
            InlineKeyboardButton("📁 New Folder", callback_data="new"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ])

        return InlineKeyboardMarkup(keyboard)

    async def start_navigation(self, client, message, on_select=None):
        try:
            logger.info(f"start_navigation base_path: {self.base_path}")

            user_id = message.from_user.id
            self.user_state_manager.set(user_id, {
                "path": self.base_path,
                "page": 0,
                "on_select": on_select
            })
            state = self.user_state_manager.get(user_id)
            logger.info(f"start_navigation state: {state}")

            keyboard = self.build_keyboard(user_id)
            await message.reply(f"📂 Browsing: `{self.base_path}`", reply_markup=keyboard)
        except Exception as e:
            logger.error(f"start_navigation Exception: {e} ")

    async def handle_callback(self, client, callback_query):
        logger.info(f"[!] FolderNavigator handle_callback callback_query : [{callback_query}] ")

        user_id = callback_query.from_user.id
        data = callback_query.data
        state = self.user_state_manager.get(user_id)
        logger.info(f"[!] handle_callback user_id : [{user_id}] ")
        logger.info(f"[!] handle_callback data : [{data}] ")
        logger.info(f"[!] handle_callback state : [{state}] ")

        if not state:
            await callback_query.answer("No active folder browsing session. Use /folders again.")
            return

        path = state["path"]

        if data == "next":
            state["page"] += 1
            self.user_state_manager.update(user_id, "page", state["page"])

        elif data == "prev":
            state["page"] -= 1
            self.user_state_manager.update(user_id, "page", state["page"])

        elif data == "up":
            parent = os.path.abspath(os.path.join(path, ".."))
            logger.info(f"[!] handle_callback up path: [{path}] ")
            logger.info(f"[!] handle_callback up parent: [{parent}] ")
            logger.info(f"[!] handle_callback up base_path: [{self.base_path}] ")
            if parent.startswith(self.base_path) or parent:
                state["path"] = parent
                state["page"] = 0
                self.user_state_manager.update(user_id, "path", state["path"])
                self.user_state_manager.update(user_id, "page", state["page"])

        elif data == "select":
            if state.get("on_select"):
                await state["on_select"](state["path"])
            await callback_query.message.edit_text(f"✅ Selected: `{state['path']}`", reply_markup=None)
            self.user_state_manager.delete(user_id)
            return

        elif data == "cancel":
            await callback_query.message.edit_text("❌ Cancelled.", reply_markup=None)
            self.user_state_manager.delete(user_id)
            return

        elif data == "new":
            await callback_query.message.edit_text("✏️ Send the name for the new folder:", reply_markup=None)
            state["awaiting_folder_name"] = True
            self.user_state_manager.update(user_id, "awaiting_folder_name", state["awaiting_folder_name"])
            return

        elif data.startswith("folder:"):
            logger.info(f"[!] startswith 1 folder state path: [{state['path']}] ")
            state = self.user_state_manager.get(user_id)
            logger.info(f"[!] startswith 2 folder state path: [{state['path']}] ")
            folder_name = data.split("folder:", 1)[1]
            new_path = os.path.join(path, folder_name)
            if os.path.isdir(new_path):
                state["path"] = new_path
                state["page"] = 0
                self.user_state_manager.update(user_id, "path", state["path"])
                self.user_state_manager.update(user_id, "page", state["page"])

        keyboard = self.build_keyboard(user_id)
        await callback_query.message.edit_text(f"📂 Browsing: `{state['path']}`", reply_markup=keyboard)

    async def handle_text(self, client, message):
        logger.info(f"[!] FolderNavigator handle_text message : [{message}] ")

        user_id = message.from_user.id
        state = self.user_state_manager.get(user_id)

        logger.info(f"[!] handle_text base_path : [{self.base_path}] ")
        logger.info(f"[!] handle_text state : [{state}] ")

        if not state or not state.get("awaiting_folder_name"):
            return

        folder_name = message.text.strip()
        if not folder_name:
            await message.reply("⚠️ Invalid folder name.")
            return

        new_folder_path = os.path.join(state["path"], folder_name)
        try:
            os.makedirs(new_folder_path, exist_ok=True)
            await message.reply(f"✅ Folder created: `{new_folder_path}`")
        except Exception as e:
            await message.reply(f"⚠️ Error creating folder:\n{e}")

        state['path'] = new_folder_path
        state.pop("awaiting_folder_name", None)
        self.user_state_manager.set(user_id, state)

        keyboard = self.build_keyboard(user_id)
        await message.reply(f"📂 Browsing: `{state['path']}`", reply_markup=keyboard)


if __name__ == "__main__":
    pass
    base_path = "/download"
    folders = [
        os.path.abspath(os.path.join(base_path, entry))
        for entry in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, entry))
    ]

    logger.info(f"[!] entries : [{folders}] ")
