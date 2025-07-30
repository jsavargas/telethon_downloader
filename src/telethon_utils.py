import logging
import os
from telethon.tl.types import PeerChannel, PeerUser

class TelethonUtils:
    def __init__(self, logger):
        self.logger = logger

    def get_origin_group(self, message):
        try:
            if message.fwd_from:
                if isinstance(message.fwd_from.from_id, PeerChannel):
                    return message.fwd_from.from_id.channel_id
                elif isinstance(message.fwd_from.from_id, PeerUser):
                    return message.fwd_from.from_id.user_id
            if message.peer_id:
                if hasattr(message.peer_id, 'channel_id') and message.peer_id.channel_id:
                    return message.peer_id.channel_id
                elif hasattr(message.peer_id, 'user_id') and message.peer_id.user_id:
                    return message.peer_id.user_id
            return "Unknown"
        except Exception as e:
            self.logger.error(f"Error in get_origin_group: {e}")
            return "Unknown"

    def get_channel_id(self, message):
        try:
            if message.fwd_from and isinstance(message.fwd_from.from_id, PeerChannel):
                return message.fwd_from.from_id.channel_id
            if message.peer_id and hasattr(message.peer_id, 'channel_id'):
                return message.peer_id.channel_id
            return None
        except Exception as e:
            self.logger.error(f"Error in get_channel_id: {e}")
            return None

    def get_file_size(self, message):
        try:
            file_size = 0
            if message.document:
                file_size = message.document.size
            elif message.photo:
                largest_size = 0
                for s in message.photo.sizes:
                    if hasattr(s, 'size') and s.size > largest_size:
                        largest_size = s.size
                file_size = largest_size
            return file_size
        except Exception as e:
            self.logger.error(f"Error in get_file_size: {e}")
            return 0

    def get_file_extension(self, message):
        try:
            file_extension = ""
            if message.document:
                file_name_attr = next((attr for attr in message.document.attributes if hasattr(attr, 'file_name')), None)
                file_name = file_name_attr.file_name if file_name_attr else 'unknown_document'
                file_extension = os.path.splitext(file_name)[1].lstrip('.')
            elif message.photo:
                file_extension = "jpg"
            return file_extension
        except Exception as e:
            self.logger.error(f"Error in get_file_extension: {e}")
            return ""

    def get_file_info(self, message):
        try:
            file_info = "media"
            if message.document:
                file_name_attr = next((attr for attr in message.document.attributes if hasattr(attr, 'file_name')), None)
                file_info = file_name_attr.file_name if file_name_attr else 'unknown_document'
            elif message.photo:
                file_info = f"photo_{message.photo.id}.jpg"
            return file_info
        except Exception as e:
            self.logger.error(f"Error in get_file_info: {e}")
            return "media"