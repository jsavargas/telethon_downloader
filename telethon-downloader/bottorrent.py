#!/usr/bin/env python3

VERSION = "VERSION 3.0.5"
HELP = """
/help		: This Screen
/version	: Version  
/sendfiles	: send files found in the /download/sendFiles folder
/id			: YOUR ID TELEGRAM
"""
UPDATE = """
- DE HASTA 2000MB
- DESCARGA DE IMAGENES COMPRESS/UNCOMPRESS
- DESCARGA DE ARCHIVOS TORRENT EN CARPETA TG_DOWNLOAD_PATH_TORRENTS
- DESCARGA DE VIDEOS/LISTAS YOUTUBE.COM Y YOUTU.BE (SOLO ENVIANDO EL LINK DEL VIDEO/LISTA)
- UPLOAD FILES IN /download/sendFiles CON EL COMANDO /sendfiles
"""

import re
import os
import shutil
import sys
import time
import asyncio
import cryptg
import youtube_dl
import threading
import zipfile

import logging
import configparser

# Imports Telethon
from telethon import TelegramClient, events
from telethon.tl import types
from telethon.utils import get_extension, get_peer_id, resolve_id

from env import api_id, api_hash, bot_token, TG_DOWNLOAD_PATH, TG_DOWNLOAD_PATH_TORRENTS, TG_UNZIP_TORRENTS, \
	YOUTUBE_LINKS_SOPORTED, TG_DOWNLOAD_PATH, SESSION, \
	TG_MAX_PARALLEL, TG_DL_TIMEOUT, PATH_TMP, PATH_COMPLETED, TG_PROGRESS_DOWNLOAD, \
	YOUTUBE_FORMAT, TG_DOWNLOAD_PATH, PATH_YOUTUBE

from logger import logger
from utils import splash, create_directory, getDownloadPath, getUsers, split_input, config_file
from youtube import youtube_download


session = SESSION


download_path = TG_DOWNLOAD_PATH
download_path_torrent = TG_DOWNLOAD_PATH_TORRENTS # Directorio bajo vigilancia de DSDownload u otro.



AUTHORIZED_USER, usuarios = getUsers()
youtube_list = split_input(YOUTUBE_LINKS_SOPORTED) 



queue = asyncio.Queue()
number_of_parallel_downloads = TG_MAX_PARALLEL
maximum_seconds_per_download = TG_DL_TIMEOUT

# Directorio temporal
tmp_path = PATH_TMP
completed_path = PATH_COMPLETED

temp_completed_path = ''

create_directory(tmp_path)
create_directory(completed_path)


FOLDER_GROUP = ''


async def tg_send_message(msg):
    if AUTHORIZED_USER: await client.send_message(usuarios[0], msg)
    return True

async def tg_send_file(CID,file,name=''):
    #await client.send_file(6537360, file)
    async with client.action(CID, 'document') as action:
    	await client.send_file(CID, file,caption=name,force_document=True,progress_callback=action.progress)
	#await client.send_message(6537360, file)

# Printing download progress
async def callback(current, total, file_path, file_name, message,_download_path=''):
	value = (current / total) * 100
	format_float = "{:.2f}".format(value)
	int_value = int(float(format_float) // 1)
	try:
		if ((int_value != 100 ) and (int_value % 20 == 0)):
			await message.edit(f'Downloading {file_name} ... {format_float}% \ndownload in:\n{_download_path}')
	finally:
		current


async def worker(name):
	while True:
		# Esperando una unidad de trabajo.

		queue_item = await queue.get()
		update = queue_item[0]
		message = queue_item[1]
		FOLDER_TO_GROUP = queue_item[2] if queue_item[2] else ''

		real_id = get_peer_id(update.message.peer_id)
		CID , peer_type = resolve_id(real_id)
		sender = await update.get_sender()
		username = sender.username

		# Comprobación de usuario
		if AUTHORIZED_USER and CID not in usuarios:
			logger.info('USUARIO: %s NO AUTORIZADO', CID)
			continue
		###
		file_path = tmp_path
		file_name = 'FILENAME'
		if isinstance(update.message.media, types.MessageMediaPhoto):
			file_name = '{}{}'.format(update.message.media.photo.id, get_extension(update.message.media))
		elif any(x in update.message.message for x in youtube_list):
			try:
				url = update.message.message
				
				logger.info(f'INIT DOWNLOADING VIDEO YOUTUBE [{url}] ')
				await youtube_download(url,update,message)
				logger.info(f'FINIT DOWNLOADING VIDEO YOUTUBE [{url}] ')
				queue.task_done()
				continue
			except Exception as e:
				logger.info('ERROR: %s DOWNLOADING YT: %s' % (e.__class__.__name__, str(e)))
				await message.edit('Error!')
				message = await message.edit('ERROR: %s DOWNLOADING YT: %s' % (e.__class__.__name__, str(e)))
				queue.task_done()
				continue
		else:
			attributes = update.message.media.document.attributes
			for attr in attributes:
				if isinstance(attr, types.DocumentAttributeFilename):
					file_name = attr.file_name
				elif update.message.message:
					file_name = re.sub(r'[^A-Za-z0-9 -!\[\]\(\)]+', ' ', update.message.message)
				else:
					file_name = time.strftime('%Y%m%d %H%M%S', time.localtime())
					file_name = '{}{}'.format(update.message.media.document.id, get_extension(update.message.media))
		file_path = os.path.join(file_path, file_name)
		_download_path, _complete_path = getDownloadPath(file_name,CID)
		logger.info(f"getDownloadPath FILE [{file_name}] to [{_download_path}]")
		await message.edit(f'Downloading {file_name} \ndownload in:\n{_download_path}')
		#time.sleep(1)
		logger.info('Downloading... ')
		mensaje = 'STARTING DOWNLOADING %s [%s] BY [%s]' % (time.strftime('%d/%m/%Y %H:%M:%S', time.localtime()), file_path , (CID))
		logger.info(mensaje)
		try:
			loop = asyncio.get_event_loop()
			if (TG_PROGRESS_DOWNLOAD == True or TG_PROGRESS_DOWNLOAD == 'True' ):
				task = loop.create_task(client.download_media(update.message, file_path, progress_callback=lambda x,y: callback(x,y,file_path,file_name,message,_download_path)))
			else:
				task = loop.create_task(client.download_media(update.message, file_path))
			download_result = await asyncio.wait_for(task, timeout = maximum_seconds_per_download)
			end_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())
			end_time_short = time.strftime('%H:%M', time.localtime())
			filename = os.path.split(download_result)[1]
			
			if FOLDER_TO_GROUP:
				final_path = os.path.join(FOLDER_TO_GROUP, filename)
				create_directory(FOLDER_TO_GROUP)
				os.chmod(FOLDER_TO_GROUP, 0o777)
			else:
				_path, final_path = getDownloadPath(filename,CID)
				create_directory(_path)
			######
			logger.info("RENAME/MOVE [%s] [%s]" % (download_result, final_path) )
			#create_directory(completed_path)
			shutil.move(download_result, final_path)
			os.chmod(final_path, 0o666)
			if TG_UNZIP_TORRENTS:
				if zipfile.is_zipfile(final_path):
					with zipfile.ZipFile(final_path, 'r') as zipObj:
						for fileName in zipObj.namelist():
							if fileName.endswith('.torrent'):
								zipObj.extract(fileName, download_path_torrent)
								logger.info("UNZIP TORRENTS [%s] to [%s]" % (fileName, download_path_torrent) )


			######
			mensaje = 'DOWNLOAD FINISHED %s [%s] => [%s]' % (end_time, file_name, final_path)
			logger.info(mensaje)
			await message.edit('Downloading finished:\n%s \nIN: %s\nat %s' % (file_name,_path,end_time_short))
		except asyncio.TimeoutError:
			logger.info('[%s] Time exceeded %s' % (file_name, time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())))
			await message.edit('Error!')
			message = await update.reply('ERROR: Time exceeded downloading this file')
		except Exception as e:
			logger.critical(e)
			logger.info('[EXCEPCION]: %s' % (str(e)))
			logger.info('[%s] Excepcion %s' % (file_name, time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())))
			await message.edit('Error!')
			message = await update.reply('ERROR: %s downloading : %s' % (e.__class__.__name__, str(e)))

		# Unidad de trabajo terminada.
		queue.task_done()

client = TelegramClient(session, api_id, api_hash, proxy = None, request_retries = 10, flood_sleep_threshold = 120)

@events.register(events.NewMessage)
async def handler(update):
	global temp_completed_path
	global FOLDER_GROUP
	try:

		real_id = get_peer_id(update.message.peer_id)
		CID , peer_type = resolve_id(real_id)

		if update.message.from_id is not None:
			logger.info("USER ON GROUP => U:[%s]G:[%s]M:[%s]" % (update.message.from_id.user_id,CID,update.message.message))

		if update.message.media is not None and ( not AUTHORIZED_USER or CID in usuarios):
			if FOLDER_GROUP != update.message.date:
				logger.info("FOLDER_GROUP => [%s][%s][%s]" % (FOLDER_GROUP,update.message.date,temp_completed_path))
				temp_completed_path  = ''

		if update.message.media is not None and ( not AUTHORIZED_USER or CID in usuarios):
			file_name = 'NONAME'

			if isinstance(update.message.media, types.MessageMediaPhoto):
				file_name = '{}{}'.format(update.message.media.photo.id, get_extension(update.message.media))
				logger.info("MessageMediaPhoto  [%s]" % file_name)
			elif any(x in update.message.message for x in youtube_list):
				file_name = 'YOUTUBE VIDEO'
			else:	
				attributes = update.message.media.document.attributes
				for attr in attributes:
					if isinstance(attr, types.DocumentAttributeFilename):
						file_name = attr.file_name
					elif update.message.message:
						file_name = re.sub(r'[^A-Za-z0-9 -!\[\]\(\)]+', ' ', update.message.message)

			mensaje = 'DOWNLOAD IN QUEUE [%s] [%s] => [%s]' % (time.strftime('%d/%m/%Y %H:%M:%S', time.localtime()),file_name,temp_completed_path)
			logger.info(mensaje)
			message = await update.reply('Download in queue...')
			await queue.put([update, message,temp_completed_path])
		elif not AUTHORIZED_USER or CID in usuarios:
			if update.message.message == '/help':
				message = await update.reply(HELP) 
				await queue.put([update, message])
			elif update.message.message == '/version': 
				message = await update.reply(VERSION)
				await queue.put([update, message,temp_completed_path])
			elif update.message.message == '/alive': 
				message = await update.reply('Keep-Alive')
				await queue.put([update, message,temp_completed_path])
			elif update.message.message == '/me' or update.message.message == '/id': 
				message = await update.reply('id: {}'.format(CID) )
				await queue.put([update, message,temp_completed_path])
				logger.info('me :[%s]' % (CID))
			else: 
				time.sleep(2)
				if '/folder' in update.message.message:
					folder = update.message.message
					FOLDER_GROUP = update.message.date
					temp_completed_path  = os.path.join(TG_DOWNLOAD_PATH,'completed',folder.replace('/folder ','')) # SI VIENE EL TEXTO '/folder NAME_FOLDER' ESTE CREARÁ UNA CARPETA Y METERÁ ADENTRO TODOS LOS ARCHIVOS A CONTINUACION 
					logger.info("DOWNLOAD FILE IN :[%s]",temp_completed_path)
				elif ((update.message.message).startswith('/sendfiles')):
					msg = await update.reply('Sending files...')
					create_directory(os.path.join(download_path,'sendFiles'))
					ignored = {"*._process"}
					basepath = os.path.join(download_path,'sendFiles')
					sending = 0
					for root, subFolder, files in os.walk(basepath):
						subFolder.sort()
						files.sort()
						for item in files:
							if item.endswith('_process') :
								#skip directories
								continue
							sending +=1
							fileNamePath = str(os.path.join(root,item))
							logger.info("SEND FILE :[%s]", fileNamePath)
							await msg.edit('Sending {}...'.format(item))
							loop = asyncio.get_event_loop()
							task = loop.create_task(tg_send_file(CID,fileNamePath,item))
							download_result = await asyncio.wait_for(task, timeout = maximum_seconds_per_download)
							#message = await tg_send_file(fileNamePath)
							shutil.move(fileNamePath, fileNamePath + "_process")
					await msg.edit('{} files submitted'.format(sending))
					logger.info("FILES SUBMITTED:[%s]", sending)
				elif ((update.message.message).startswith('#')):
					folder = update.message.message
					FOLDER_GROUP = update.message.date
					temp_completed_path  = os.path.join(TG_DOWNLOAD_PATH,'completed',folder.replace('#','')) # SI VIENE EL TEXTO '/folder NAME_FOLDER' ESTE CREARÁ UNA CARPETA Y METERÁ ADENTRO TODOS LOS ARCHIVOS A CONTINUACION 
					logger.info("DOWNLOAD FILE IN :[%s]",temp_completed_path)

		elif update.message.message == '/me' or update.message.message == '/id':
			logger.info('UNAUTHORIZED USER: %s ', CID)
			message = await update.reply('UNAUTHORIZED USER: %s \n add this ID to TG_AUTHORIZED_USER_ID' % CID)
	except Exception as e:
		message = await update.reply('ERROR: ' + str(e))
		logger.info('EXCEPTION USER: %s ', str(e))





if __name__ == '__main__':

	try:

		# Crear cola de procesos concurrentes.
		tasks = []
		for i in range(number_of_parallel_downloads):
			loop = asyncio.get_event_loop()
			task = loop.create_task(worker('worker-{%i}' %i))
			tasks.append(task)

		# Arrancamos bot con token
		client.start(bot_token=str(bot_token))
		client.add_event_handler(handler)

		# Pulsa Ctrl+C para detener
		loop.run_until_complete(tg_send_message("Telethon Downloader Started: {}".format(VERSION)))
		logger.info("%s" % VERSION)
		config_file()
		logger.info("********** START TELETHON DOWNLOADER **********")

		client.run_until_disconnected()
	finally:
		# Cerrando trabajos.
		
	#f.close()
		for task in tasks:
			task.cancel()
		# Cola cerrada
		# Stop Telethon
		client.disconnect()
		logger.info("********** STOPPED **********")
	
