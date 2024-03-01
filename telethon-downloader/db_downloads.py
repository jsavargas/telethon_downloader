import json
import os
from datetime import datetime
from constants import EnvironmentReader
import logger


class DownloadFilesDB:
    def __init__(self):
        self.constants = EnvironmentReader()
        self.json_file = self.constants.get_variable("PATH_DOWNLOAD_FILES")
        self.downloads = self.load_from_json()
        self.limit = 500

    def add_download_files(self, user_id, event_id, message_id, original_filename):
        download_info = {
            "user_id": user_id,
            "event_id": event_id,
            "message_id": message_id,
            "original_filename": original_filename,
            "new_filename": None,
            "download_date": str(datetime.now()),
            "update_date": None,  # Will be updated when necessary
        }

        # Add download information
        self.downloads.append(download_info)

        # Save to the JSON file
        self.save_to_json()

    def update_download_files(self, message_id, new_filename):
        logger.logger.info(
            f"update_download_files => record: {message_id}, {new_filename}"
        )

        try:
            for record in self.downloads:
                if (
                    record["message_id"] == message_id
                    or record["event_id"] == message_id
                ):
                    record["new_filename"] = new_filename
                    record["update_date"] = str(datetime.now())

                    self.save_to_json()

                    return True
            return False

        except Exception as e:
            logger.logger.info(f"update_download_files => Exception: {e}")
            return None

    def save_to_json(self):
        with open(self.json_file, "w") as file:
            json.dump(self.downloads[-self.limit :], file, indent=2)

    def load_from_json(self):
        try:
            with open(self.json_file, "r") as json_file:
                data = json.load(json_file)
                return data[-500:]

        except FileNotFoundError:
            return []
        except Exception as e:
            return []

    def get_download_file(self, message_id):
        found_element = next(
            (
                download_info
                for download_info in self.downloads
                if download_info["message_id"] == message_id
                or download_info["event_id"] == message_id
            ),
            None,
        )
        return found_element
