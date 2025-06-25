# -*- coding: utf-8 -*-
#print("\033c")

import os
import re
import time
from datetime import datetime
import logging
import asyncio
import yt_dlp
import shutil

from pyrogram import Client, errors, idle, filters, __version__ as pyrogram_version
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait, RPCError, AuthBytesInvalid


from env import Env
from utils import Utils 
from logger_config import logger, get_last_error_log
from print_handler import PartialPrinter
from data_handler import FileDataHandler
from downloadPathManager import DownloadPathManager
from command_handler import CommandHandler
from url_downloader import URLDownloader
from pending_handler import PendingMessagesHandler
from info_handler import InfoMessages


logger.info(f"Starting Telegram Downloader Bot Started : {datetime.now():%Y/%m/%d %H:%M:%S}")

class Config:
    def __init__(self):
        self.BOT_VERSION = "5.0.0-r2"
        self.PYROGRAM_VERSION = pyrogram_version
        self.YT_DLP_VERSION = yt_dlp.version.__version__


config = Config()

env = Env()
utils = Utils()
print_handler = PartialPrinter()
downloadFilesDB = FileDataHandler()
downloadPathManager = DownloadPathManager()
command_handler = CommandHandler(config)
url_downloader = URLDownloader()
pendingMessagesHandler = PendingMessagesHandler()
info_handler = InfoMessages()

utils.removeFiles()

msg_txt = ""
app = Client("telegramBot", api_id=int(env.API_ID), api_hash=env.API_HASH, bot_token=env.BOT_TOKEN, workers=env.WORKERS, max_concurrent_transmissions=env.MAX_CONCURRENT_TRANSMISSIONS)


# Semaphore to limit the number of simultaneous downloads
semaphore = asyncio.Semaphore(int(env.MAX_CONCURRENT_TASKS))


while True:
    try:
        with app:
            msg_txt = "Telegram Downloader Bot Started\n\n"
            msg_txt += f"bot version: {config.BOT_VERSION}\n"
            msg_txt += f"pyrogram version: {pyrogram_version}\n"
            msg_txt += f"yt_dlp version: {yt_dlp.version.__version__}\n"
            
            logger.info(f"Telegram Downloader Bot Started : {datetime.now():%Y/%m/%d %H:%M:%S}")
            app.send_message(int(env.AUTHORIZED_USER_ID[0]), msg_txt)
            print_handler.print_variable("BOT_VERSION", config.BOT_VERSION)
            print_handler.print_variable("PYROGRAM_VERSION", pyrogram_version)
            print_handler.print_variable("YTDLP_VERSION", yt_dlp.version.__version__)
            print_handler.print_variables()
            break 
    except FloodWait as e:
        logger.info(f"FloodWait: Esperando {e.value} segundos antes de reintentar iniciar...\n {e}")
        remaining_time = e.value + 10
        while remaining_time > 0:
            logger.info(f"Remaining time: {remaining_time} seconds")
            time.sleep(60)
            remaining_time -= 60



def message2file(message: Message) -> str:

    if not env.MESSAGE_FILE:
        return False
    logger.info(f"message2file [{env.MESSAGE_FILE}]")
    logger.info(f"message2file [{os.path.join(env.CONFIG_PATH, "messages.txt")}]")
    message_str = str(message)
    with open(os.path.join(env.CONFIG_PATH, "messages.txt"), "a") as file:
        file.write(f"MESSAGE_FILE:: {datetime.now():%Y/%m/%d %H:%M:%S}\n{message_str}\n\n\n\n")

@app.on_message(filters.document | filters.photo | filters.video | filters.audio | filters.animation)
async def handle_files(client: Client, message: Message):
    try:
        pendingMessagesHandler.add_pending_message(message.id, message)
        
        attempt = 0
        file_path = ""

        async with semaphore:
                logger.info("Start Download")
                message2file(message)
                
                user_id = info_handler.get_userId(message)
                origin_group = info_handler.get_originGroup(message) 

                if user_id and str(user_id) in env.AUTHORIZED_USER_ID:
                    start_msg = await message.reply_text(f"Pendiente de descarga: ", reply_to_message_id=message.id)
                    
                    file_name = info_handler.getFileName(message)
                    _FileSize = info_handler.getFileSize(message)

                    file_name, download_path = downloadPathManager.getDownloadPath(message, origin_group, file_name)
                    #file_name = downloadPathManager.getDownloadFilename(message, origin_group, file_name)

                    
                    start_time, start_hour = utils.startTime()

                    summary = f"**Downloading file:**"
                    summary += f"\n\n**File Name:** {file_name}"
                    if download_path: summary += f"\n**Download Folder:** {download_path}"
                    if start_hour: summary += f"\n**Start Time:** {start_hour}"
                    if _FileSize: summary += f"\n**File Size:** {utils.format_size(_FileSize)}"
                    if origin_group: summary += f"\n**Origin Group:** {origin_group}"



                    await start_msg.edit_text(summary)

                    file_name_download = os.path.join(download_path, file_name)


                    #while attempt < env.MAX_RETRIES:
                    while attempt < 100:
                        try:
                            if os.path.exists(file_name_download) and os.path.getsize(file_name_download) != 0 and os.path.getsize(file_name_download) != _FileSize:
                                directory, filename = os.path.split(file_name_download)
                                name, ext = os.path.splitext(filename)
                                file_name = f"{name}_2{ext}"
                                file_name_download = os.path.join(directory, file_name)

                            DOWNLOAD_INCOMPLETED_PATH = os.path.join(env.DOWNLOAD_INCOMPLETED_PATH, file_name)

                            utils.create_folders(DOWNLOAD_INCOMPLETED_PATH)
                            utils.create_folders(file_name_download)

                            logger.info(f"[****] File download start file_name_download: [{attempt}]  [{DOWNLOAD_INCOMPLETED_PATH}]")
                            if env.PROGRESS_DOWNLOAD:
                                file_path = await message.download(file_name=DOWNLOAD_INCOMPLETED_PATH, progress=progress_callback(start_msg, summary))
                            else:
                                file_path = await message.download(file_name=DOWNLOAD_INCOMPLETED_PATH)

                            tempFilename = command_handler.getTempFilename(client, message)
                            if tempFilename:
                                file_name = tempFilename
                                file_name_download = os.path.join(download_path, file_name)
                            logger.info(f"[****] File download tempFilename: [{tempFilename}]  [{file_name_download}]")

                            if _FileSize == os.path.getsize(file_path):
                                shutil.move(file_path, file_name_download)

                                file_path = file_name_download

                                logger.info(f"[****] File download finish: [{attempt}] {file_path},  [{_FileSize}] == [{os.path.getsize(file_path)}] => [{message.id}]")
                                pendingMessagesHandler.remove_pending_message(message.id, message)
                                downloadFilesDB.add_download_files(file_path, message)
                                break

                            last_error_log = get_last_error_log()
                            
                            if 'ERROR' in last_error_log:
                                logger.warning(f"[!!] LAST ERROR WARNING [ERROR]: {file_path}  last_error_log [{last_error_log}]")
                                time.sleep(1)

                            if '400 AUTH_BYTES_INVALID' in last_error_log:
                                logger.warning(f"[!!] LAST ERROR WARNING [400 AUTH_BYTES_INVALID]: [{file_path}  last_error_log [{last_error_log}]")
                                time.sleep(1)

                            elif '-503 Timeout' in last_error_log:
                                logger.warning(f"[!!] LAST ERROR WARNING [-503 Timeout]: [{file_path}  last_error_log [{last_error_log}]")
                                await start_msg.edit_text(f"Downloading file: {file_name} \n-503 Timeout. Please try this file again later")
                                return
                                break
                            
                            elif os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                                attempt += 1
                                logger.warning(f"[!!] File download failed: {file_path}, getsize: {os.path.getsize(file_path)} attempt: {attempt}")
                                await start_msg.edit_text(f"Downloading file: {file_name} \nwait 60 seconds\nretry: {attempt}")
                                time.sleep(60)
                            else:
                                logger.warning(f"[!!] File download FloodWait: [{attempt}] {file_path}  _FileSize [{_FileSize}] getsize: [{os.path.getsize(file_path)}]")
                                time.sleep(30)


                        except FloodWait as e:
                            logger.warning(f"FloodWait Exception: {e} ")
                            await message.reply_text(f"Downloading file FloodWait: {e}", reply_to_message_id=message.id)
                            time.sleep(60)

                        except RPCError as e:
                            logger.warning(f"FloodWait RPCError: {e} ")
                            await message.reply_text(f"Downloading file RPCError: {e}", reply_to_message_id=message.id)
                            time.sleep(60)

                        except errors.exceptions.bad_request_400.AuthBytesInvalid as e:
                            logger.warning(f"FloodWait AuthBytesInvalid: {e} ")
                            await message.reply_text(f"Downloading file AuthBytesInvalid: {e}", reply_to_message_id=message.id)
                            time.sleep(60)

                        except Exception as e:
                            logger.error(f"Exception Exception: {e} ")
                            #await message.reply_text(f"Downloading file Exception: {e}", reply_to_message_id=message.id)
                            attempt += 1
                            logger.error(f"Attempt {attempt} failed: {e}")
                            time.sleep(60)
                            if attempt == env.MAX_RETRIES:
                                logger.error("Maximum retries reached. Download failed.")


                    if not _FileSize == os.path.getsize(file_path):
                        await start_msg.edit_text(f"Downloading failed: {file_name}\nretry: {attempt}")
                        return False
                    

                    utils.change_permissions(download_path)
                    utils.change_permissions(file_path)

                    end_time, end_hour = utils.endTime()
                    elapsed_time = utils.elapsedTime(start_time, end_time)
                    file_size, size_str = utils.getSize(file_path)
                    download_speed = file_size / elapsed_time / 1024  # KB/s

                    download_info = {
                        'file_name': file_name,
                        'download_folder': download_path,
                        'size_str': size_str,
                        'start_hour': start_hour,
                        'end_hour': end_hour,
                        'elapsed_time': elapsed_time,
                        'download_speed': download_speed,
                        'origin_group': message.forward_from.id if message.forward_from else message.forward_from_chat.id if message.forward_from_chat else None ,
                        'retries': attempt,
                        'message': message
                    }

                    summary = utils.create_download_summary(download_info)
                    await start_msg.edit_text(summary)
                if env.IS_DELETE: await message.delete()

    except Exception as e:
        logger.error(f"handle_files Exception: {e} ")
        await message.reply_text(f"handle_files file Exception: {e}", reply_to_message_id=message.id)


def progress_callback(message, summary):
    """Callback function to report download progress."""
    async def callback(current, total):

        if not env.PROGRESS_DOWNLOAD:
            return
        
        nonlocal last_percentage

        percent = int(current / total * 100)
        rounded_percent = (percent // 10) * 10

        try:

            if rounded_percent % int(env.PROGRESS_STATUS_SHOW) == 0:
                if last_percentage == rounded_percent:
                    return 
                       
                logger.info(f"progress_callback percent: message: [{message.id}] {percent} ==> [{rounded_percent}] ")     
                
                last_percentage = rounded_percent

                await message.edit(f"{summary}\n**Progress:** {rounded_percent} %")
        except Exception as e:
            logger.info(f"progress_callback Exception  => : {e} ")
            pass
    last_percentage = -1
    return callback


@app.on_message(filters.media)
async def download(client: Client, message: Message):
    logger.info(f"No soportado : {message}")


@app.on_message(filters.command(command_handler.command_keys))
async def handle_commands(client: Client, message: Message):
    logger.info(f"handle_commands : {message}")
    message2file(message)
    await command_handler.process_command(client, message)


@app.on_message(filters.text)
async def handle_text_messages(client, message: Message):
    logger.info(f"handle_text_messages : {message}")
    # Regex to detect URLs in a message
    URL_REGEX = re.compile(r'https?://\S+')
    async with semaphore:
        urls = URL_REGEX.findall(message.text)
        if urls:
            for url in urls:
                await url_downloader.download_from_url(client, message, url)  # Use the class method


@app.on_callback_query(filters.regex(r'^ytdown_.*'))
async def handle_callback_query(client, callback_query: CallbackQuery):
    await url_downloader.handle_callback_query(client, callback_query)


if __name__ == "__main__":

    logger.info("Telegram Downloader Bot Started")
    #app.run()

    app.start()
    idle()
    app.stop()

    logger.info("Telegram Downloader Bot Finish")
