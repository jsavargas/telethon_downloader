import os
import json

from logger_config import logger

class UserStateManager:
    def __init__(self, filepath="/config/user_states.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                logger.error(f"[!] Error loading JSON: {e}")
                return {}
        return {}

    def _save(self):
        logger.info(f"[!] UserStateManager _save : [{self._data}]")
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def set(self, user_id, state):
        logger.info(f"[!] UserStateManager set : [{state}]")
        self._data[str(user_id)] = state
        self._save()

    def get(self, user_id, default=None):
        self._data = self._load()  # Siempre recarga desde el archivo
        logger.info(f"[!] UserStateManager get : [{self._data}]")
        return self._data.get(str(user_id), default)

    def delete(self, user_id):
        logger.info(f"[!] UserStateManager delete : [{self._data}]")
        if str(user_id) in self._data:
            del self._data[str(user_id)]
            self._save()

    def update(self, user_id, key, value):
        if str(user_id) in self._data:
            self._data[str(user_id)][key] = value
            self._save()

    def get_all(self):
        return self._data

    def clear(self):
        self._data = {}
        self._save()
