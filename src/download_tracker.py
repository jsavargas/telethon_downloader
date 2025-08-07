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

    def add_download(self, initial_bot_message_id, message_id, initial_filename, media, channel_id, user_id, filename, download_type='file', current_file_path=None):
        if download_type != 'file':
            self.logger.info(f"Skipping saving non-file download to tracker: {message_id} (Type: {download_type})")
            return

        data = self._read_data()
        for entry in data:
            if entry.get('message_id') == message_id and entry.get('channel_id') == channel_id:
                self.logger.warning(f"Download with message_id {message_id} and channel_id {channel_id} already exists. Skipping.")
                return

        new_entry = {
            "initial_bot_message_id": initial_bot_message_id,
            "message_id": message_id,
            "initial_filename": initial_filename,
            "filename": filename,
            "download_date": datetime.now().isoformat(),
            "new_filename": None,
            "update_date": None,
            "media": str(media),
            "status": "downloading",
            "channel_id": channel_id,
            "user_id": user_id,
            "download_type": download_type,
            "current_file_path": current_file_path
        }
        
        data.append(new_entry)
        self._write_data(data)
        self.logger.info(f"Added new download to tracker: {message_id}")

    def update_status(self, message_id, new_status, final_filename=None, download_type='file'):
        if download_type != 'file':
            self.logger.info(f"Skipping updating status for non-file download: {message_id} (Type: {download_type})")
            return

        data = self._read_data()
        for entry in data:
            if entry['message_id'] == message_id:
                entry['status'] = new_status
                if new_status == 'completed':
                    entry['download_date'] = datetime.now().isoformat()
                    if final_filename:
                        entry['current_file_path'] = final_filename
                if final_filename:
                    entry['new_filename'] = final_filename
                self._write_data(data)
                self.logger.info(f"Updated download status for {message_id} to {new_status}")
                return
        self.logger.warning(f"Could not find download with message_id {message_id} to update status.")

    def get_pending_downloads(self):
        data = self._read_data()
        return [d for d in data if d.get('status') == 'downloading' and d.get('download_type') == 'file']

    def get_download_by_message_id(self, message_id):
        data = self._read_data()
        for entry in data:
            if entry.get('message_id') == message_id or entry.get('initial_bot_message_id') == message_id:
                return entry
        return None

    def remove_download(self, message_id, download_type='file'):
        if download_type != 'file':
            self.logger.info(f"Skipping removing non-file download from tracker: {message_id} (Type: {download_type})")
            return

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
