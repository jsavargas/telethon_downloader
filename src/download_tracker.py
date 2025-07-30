import json
import os
from datetime import datetime

class DownloadTracker:
    def __init__(self, config_path, logger):
        self.file_path = os.path.join(config_path, 'download-files.json')
        self.logger = logger
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    def _read_data(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_data(self, data):
        with open(self.file_path, 'w') as f:
            # Keep only the last 500 entries
            json.dump(data[-500:], f, indent=2)

    def add_download(self, media_group_id, message_id, original_filename, media, channel_id, user_id, filename):
        data = self._read_data()
        for entry in data:
            if entry.get('message_id') == message_id and entry.get('channel_id') == channel_id:
                self.logger.warning(f"Download with message_id {message_id} and channel_id {channel_id} already exists. Skipping.")
                return

        new_entry = {
            "media_group_id": media_group_id,
            "message_id": message_id,
            "original_filename": original_filename,
            "filename": filename,
            "download_date": datetime.now().isoformat(),
            "new_filename": None,
            "update_date": None,
            "media": str(media),
            "status": "downloading",
            "channel_id": channel_id,
            "user_id": user_id
        }
        
        data.append(new_entry)
        self._write_data(data)
        self.logger.info(f"Added new download to tracker: {message_id}")

    def update_status(self, message_id, new_status, new_filename=None):
        data = self._read_data()
        for entry in data:
            if entry['message_id'] == message_id:
                entry['status'] = new_status
                if new_status == 'completed':
                    entry['download_date'] = datetime.now().isoformat()
                if new_filename:
                    entry['original_filename'] = new_filename
                self._write_data(data)
                self.logger.info(f"Updated download status for {message_id} to {new_status}")
                return
        self.logger.warning(f"Could not find download with message_id {message_id} to update status.")

    def get_pending_downloads(self):
        data = self._read_data()
        return [d for d in data if d.get('status') == 'downloading']

    def get_download_by_message_id(self, message_id):
        data = self._read_data()
        for entry in data:
            if entry['message_id'] == message_id:
                return entry
        return None

    def remove_download(self, message_id):
        data = self._read_data()
        initial_len = len(data)
        data = [entry for entry in data if entry.get('message_id') != message_id]
        if len(data) < initial_len:
            self._write_data(data)
            self.logger.info(f"Removed download with message_id {message_id} from tracker.")
        else:
            self.logger.warning(f"Could not find download with message_id {message_id} to remove.")

    def clear_pending_downloads(self):
        data = self._read_data()
        cleared_data = [d for d in data if d.get('status') != 'downloading']
        self._write_data(cleared_data)
        self.logger.info("Cleared all pending downloads.")
