import json

from constants import EnvironmentReader


class PendingMessagesHandler:
    def __init__(self):
        self.constants = EnvironmentReader()
        self.file_name = self.constants.get_variable("PATH_PENDING_MESSAGES")
        self.pending_messages = []
        self.load_from_json()

    def add_pending_message(self, user_id, message):
        if any(
            item["user_id"] == user_id and item["message"] == message
            for item in self.pending_messages
        ):
            pass
        else:
            self.pending_messages.append({"user_id": user_id, "message": message})
            self.save_to_json()

    def remove_pending_message(self, user_id, message):
        self.pending_messages = [
            item
            for item in self.pending_messages
            if not (item["user_id"] == user_id and item["message"] == message)
        ]

        self.save_to_json()

    def save_to_json(self):
        with open(self.file_name, "w") as json_file:
            json.dump(self.pending_messages, json_file)

    def load_from_json(self):
        try:
            with open(self.file_name, "r") as json_file:
                loaded_messages = json.load(json_file)
                self.pending_messages = loaded_messages
                return loaded_messages
        except FileNotFoundError:
            return []

        except Exception as e:
            return []

    def get_pending_messages(self):
        return self.pending_messages
