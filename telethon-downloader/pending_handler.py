import json
import asyncio

from env import Env


class PendingMessagesHandler:
    def __init__(self):
        self.env = Env()
        self.data_path = self.env.PENDING_FILES_DB
        self.pending_messages = {}
        self.load_from_json()

    def add_pending_message(self, user_id, message):

        try:
            self.pending_messages[user_id] = {
                "user_id": user_id,
                "message": str(message),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            self.save_to_json()
        except Exception as e:
            print(f"add_pending_message Exception: {user_id}, {e}")

    def remove_pending_message(self, user_id, message):
        try:
            del self.pending_messages[user_id]
            self.save_to_json()
        except Exception as e:
            print(f"remove_pending_message Exception: {user_id}, {e}")

    
    def save_to_json(self):
        with open(self.data_path, "w") as json_file:
            json.dump(self.pending_messages, json_file, indent=4)
    

    def load_from_json(self):
        try:
            with open(self.data_path, "r") as json_file:
                loaded_messages = json.load(json_file)
                self.pending_messages = loaded_messages
                return loaded_messages
        except FileNotFoundError:
            return []

        except Exception as e:
            return []

    def get_pending_messages(self):
        return self.pending_messages
