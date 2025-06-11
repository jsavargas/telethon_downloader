import os
import time
import shutil
from pyrogram.types import Message

from env import Env
from utils import Utils 

utils = Utils()
env = Env()

async def download_file(message: Message) -> str:
    file_name = get_file_name(message)
    start_time = time.time()
    start_hour = time.strftime("%H:%M:%S", time.localtime(start_time))

    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:


            temp_download_path = utils.getDownloadFolderTemp(file_name)
            #print(f"temp_download_path: {temp_download_path}")
            download_folder, file_name_download = utils.getDownloadFolder(file_name)
            #print(f"download_folder: {temp_download_path} file_name_download: {file_name_download}")

            file_path = await message.download(file_name=file_name_download, block=True)
            #print(f"file_path: {temp_file_path}")
            #file_path = shutil.move(temp_file_path, file_name_download)
            #print(f"shutil: {file_path}")

            end_time = time.time()
            end_hour = time.strftime("%H:%M:%S", time.localtime(end_time))

            elapsed_time = end_time - start_time
            file_size = os.path.getsize(file_path)
            download_speed = file_size / elapsed_time / 1024  # KB/s

            size_str = utils.format_file_size(file_size)
            
            download_info = {
                'file_name': file_name,
                'download_folder': download_folder,
                'size_str': size_str,
                'start_hour': start_hour,
                'end_hour': end_hour,
                'elapsed_time': elapsed_time,
                'download_speed': download_speed,
                'origin_group': message.chat.id if message.chat else None,
                'retries': attempt
            }
            
            print(f"get_file_name: {file_name}, {file_size}")

            if file_size <= 0:
                attempt += 1
            else:
                summary = utils.create_download_summary(download_info)
                
                utils.change_permissions_owner(file_path)

                return summary

        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                return f"Error al descargar **{file_name}**: {str(e)}. Máximo número de intentos alcanzado."

        time.sleep(2)  # Esperar 2 segundos antes de reintentar

    return f"Error al descargar **{file_name}**."

def get_file_name(message: Message) -> str:
    if message.document:
        return message.document.file_name
    elif message.photo:
        return f"{message.photo.file_unique_id}.jpg"
    elif message.video:
        return message.video.file_name
    elif message.audio:
        return message.audio.file_name
    else:
        return "Archivo"


