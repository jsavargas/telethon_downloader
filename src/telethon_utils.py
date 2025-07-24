import os

class TelethonUtils:
    @staticmethod
    def get_origin_group(message):
        origin_group = "Unknown"
        if message.peer_id:
            if hasattr(message.peer_id, 'channel_id') and message.peer_id.channel_id:
                origin_group = message.peer_id.channel_id
            elif hasattr(message.peer_id, 'user_id') and message.peer_id.user_id:
                origin_group = message.peer_id.user_id
        return origin_group

    @staticmethod
    def get_file_size(message):
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

    @staticmethod
    def get_file_extension(message):
        file_extension = ""
        if message.document:
            file_name_attr = next((attr for attr in message.document.attributes if hasattr(attr, 'file_name')), None)
            file_name = file_name_attr.file_name if file_name_attr else 'unknown_document'
            file_extension = os.path.splitext(file_name)[1].lstrip('.')
        elif message.photo:
            file_extension = "jpg"
        return file_extension

    @staticmethod
    def get_file_info(message):
        file_info = "media"
        if message.document:
            file_name_attr = next((attr for attr in message.document.attributes if hasattr(attr, 'file_name')), None)
            file_info = file_name_attr.file_name if file_name_attr else 'unknown_document'
        elif message.photo:
            file_info = f"photo_{message.id}.jpg"
        return file_info