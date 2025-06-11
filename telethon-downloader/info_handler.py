from pyrogram.types import Message
from logger_config import logger

import os

class InfoMessages:
    def __init__(self):
        self.data = []


    def get_userId(self, message: Message):
        try:
            return message.from_user.id if message.from_user else None
        except Exception as e:
            logger.error(f"get_userId Exception: {e} ")
            raise Exception(f"get_userId Exception: {e} ")

    def get_originGroup(self, message: Message):
        try:
            return message.forward_from.id if message.forward_from else message.forward_from_chat.id if message.forward_from_chat else None
        except Exception as e:
            logger.error(f"get_originGroup Exception: {e} ")
            raise Exception(f"get_originGroup Exception: {e} ")


    def getFileName(self, message: Message) -> str:
        if message.document:
            return message.document.file_name
        elif message.photo:
            return f"{message.photo.file_unique_id}.jpg"
        elif message.video:
            return message.video.file_name if message.video.file_name else f"{message.video.file_unique_id}.{message.video.mime_type.split('/')[-1]}"
        elif message.animation:
            return message.animation.file_name if message.animation.file_name else f"{message.animation.file_unique_id}.{message.animation.mime_type.split('/')[-1]}"
        elif message.audio:
            return message.audio.file_name or f"{message.audio.title}.{message.audio.mime_type.split('/')[1].replace('x-', '')}" or f"{message.audio.file_unique_id}.{message.audio.mime_type.split('/')[1].replace('x-', '')}"
        else:
            return "Archivo"

    def getFileExtension(self, message: Message) -> str:
        if message.document:
            name, extension = os.path.splitext(message.document.file_name)
            return extension
        elif message.photo:
            return "jpg"
        elif message.video:
            return os.path.splitext(message.video.file_name)[1] if message.video.file_name else f"{message.video.mime_type.split('/')[-1]}"
        elif message.animation:
            return os.path.splitext(message.animation.file_name)[1] if message.animation.file_name else f"{message.animation.mime_type.split('/')[-1]}"
        elif message.audio:
            return os.path.splitext(message.audio.file_name)[1] if message.audio.file_name else f"{message.audio.mime_type.split('/')[1].replace('x-', '')}"
        else:
            return None

    def getFileSize(self, message: Message) -> str:
        if message.document:
            #logger.info(f"message.document: {message.document}")
            return message.document.file_size
        elif message.photo:
            #logger.info(f"message.photo: {message.photo}")
            return message.photo.file_size
        elif message.video:
            #logger.info(f"message.video: {message.video}")
            return message.video.file_size #if message.video.file_size else f"{message.video.file_unique_id}.{message.video.mime_type.split('/')[-1]}"
        elif message.animation:
            #logger.info(f"message.animation: {message.animation}")
            return message.animation.file_size #if message.animation.file_size else f"{message.animation.file_unique_id}.{message.animation.mime_type.split('/')[-1]}"
        elif message.audio:
            #logger.info(f"message.audio: {message.audio}")
            return message.audio.file_size #if message.audio.file_name else f"{message.audio.title}.{message.audio.mime_type[-3:]}"
        else:
            #logger.info(f"message: {message}")
            return 0

    def validateMessage(self, message: Message) -> bool:
        if message.document:
            return True
        elif message.photo:
            logger.info(f"validateMessage message.photo")
            return True
        elif message.video:
            logger.info(f"validateMessage message.video")
            return True
        elif message.animation:
            logger.info(f"validateMessage message.animation")
            return True
        elif message.audio:
            logger.info(f"validateMessage message.audio")
            return True
        else:
            logger.info(f"validateMessage else")
            return False

    def getDataMessage(self, message: Message) -> bool:
        if message.document:
            return message.document if message.document else None
        elif message.photo:
            logger.info(f"getDataMessage message.photo")
            return message.photo if message.photo else None
            return True
        elif message.video:
            logger.info(f"getDataMessage message.video")
            return message.video if message.video else None
            return True
        elif message.animation:
            logger.info(f"getDataMessage message.animation")
            return message.animation if message.animation else None
            return True
        elif message.audio:
            return message.audio if message.audio else None
            logger.info(f"getDataMessage message.audio")
            return True
        else:
            logger.info(f"getDataMessage else")
            return None


    def get_originGroup_test(self, message: Message):
        try:

            if message.forward_from_chat:
                return message.forward_from_chat.id

            elif message.reply_to_message:
                reply_to_message = message.reply_to_message


                return reply_to_message.forward_from.id if reply_to_message.forward_from else reply_to_message.forward_from_chat.id if reply_to_message.forward_from_chat else None

            elif message.forward_from:
                return message.forward_from.id if message.forward_from else message.forward_from_chat.id if message.forward_from_chat else None
            
            else:
                return message.from_user.id

        except Exception as e:
            logger.error(f"get_originGroup_test Exception: {e} ")
            raise Exception(f"get_originGroup_test Exception: {e} ")


