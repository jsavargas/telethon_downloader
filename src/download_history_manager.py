import json
import os
import logging

class DownloadHistoryManager:
    def __init__(self, history_file_path, max_entries=500):
        self.history_file_path = history_file_path
        self.max_entries = max_entries
        self.logger = logging.getLogger(__name__)
        self.history = self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file_path):
            with open(self.history_file_path, 'r') as f:
                try:
                    history_data = json.load(f)
                    if isinstance(history_data, list):
                        return history_data
                    else:
                        self.logger.warning(f"Download history file {self.history_file_path} contains invalid format (not a list). Initializing with empty list.")
                        return []
                except json.JSONDecodeError:
                    self.logger.warning(f"Download history file {self.history_file_path} is corrupted or empty. Initializing with empty list.")
                    return []
        return []

    def _save_history(self):
        with open(self.history_file_path, 'w') as f:
            json.dump(self.history, f, indent=4)

    def add_or_update_entry(self, entry_data):
        message_id = entry_data.get('message_id')
        if message_id is None:
            self.logger.error("Entry data must contain a 'message_id' to be added or updated.")
            return

        found = False
        for i, entry in enumerate(self.history):
            if entry.get('message_id') == message_id:
                self.history[i] = entry_data
                found = True
                break
        
        if not found:
            self.history.append(entry_data)
            if len(self.history) > self.max_entries:
                self.history = self.history[-self.max_entries:]
        self._save_history()

    def get_history(self):
        return self.history