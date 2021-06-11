#!/usr/bin/env python3

VERSION = "VERSION 2.8"
HELP = """
/help		: This Screen
/alive		: keep-alive
/version	: Version  
/sendfiles	: send files found in the /download/sendFiles folder
/me			: YOUR ID TELEGRAM   
"""
UPDATE = """BASADO EN EL BOT DE @De 2021:
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
# Imports Telethon
from telethon import TelegramClient, events
from telethon.tl import types
from telethon.utils import get_extension, get_peer_id, resolve_id
import youtube_dl
import threading

import logging

'''
LOGGER
'''

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)-7s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Variables de cada usuario ######################
# This is a helper method to access environment variables or
# prompt the user to type them in the terminal if missing.
def get_env(name, message, cast=str):
	if name in os.environ:
		logger.info('%s: %s' % (name , os.environ[name]))
		return os.environ[name]
	else:
		logger.info('%s: %s' % (name , message))
		return message


# Define some variables so the code reads easier
session = os.environ.get('TG_SESSION', 'bottorrent')
api_id = get_env('TG_API_ID', 'Enter your API ID: ', int)
api_hash = get_env('TG_API_HASH', 'Enter your API hash: ')
bot_token = get_env('TG_BOT_TOKEN', 'Enter your Telegram BOT token: ')
TG_AUTHORIZED_USER_ID = get_env('TG_AUTHORIZED_USER_ID', False)
TG_DOWNLOAD_PATH = get_env('TG_DOWNLOAD_PATH', '/download')
TG_DOWNLOAD_PATH_TORRENTS = get_env('TG_DOWNLOAD_PATH_TORRENTS', '/watch')
YOUTUBE_LINKS_SOPORTED = get_env('YOUTUBE_LINKS_SOPORTED', 'youtube.com,youtu.be')

download_path = TG_DOWNLOAD_PATH
download_path_torrent = TG_DOWNLOAD_PATH_TORRENTS # Directorio bajo vigilancia de DSDownload u otro.

usuarios = list(map(int, TG_AUTHORIZED_USER_ID.replace(" ", "").split(','))) if TG_AUTHORIZED_USER_ID else False 
youtube_list = list(map(str, YOUTUBE_LINKS_SOPORTED.replace(" ", "").split(','))) 


queue = asyncio.Queue()
number_of_parallel_downloads = int(os.environ.get('TG_MAX_PARALLEL',4))
maximum_seconds_per_download = int(os.environ.get('TG_DL_TIMEOUT',3600))

# Directorio temporal
tmp_path = os.path.join(download_path,'tmp')
completed_path = os.path.join(download_path,'completed')
temp_completed_path = ''

os.makedirs(tmp_path, exist_ok = True)
os.makedirs(completed_path, exist_ok = True)
os.makedirs(os.path.join(download_path,'mp3'), exist_ok = True)
os.makedirs(os.path.join(download_path,'pdf'), exist_ok = True)
os.makedirs(os.path.join(download_path,'torrent'), exist_ok = True)
os.makedirs(os.path.join(download_path,'sendFiles'), exist_ok = True)

FOLDER_GROUP = ''

async def tg_send_message(msg):
    if TG_AUTHORIZED_USER_ID: await client.send_message(usuarios[0], msg)
    return True

async def tg_send_file(CID,file,name=''):
    #await client.send_file(6537360, file)
    async with client.action(CID, 'document') as action:
    	await client.send_file(CID, file,caption=name,force_document=True,progress_callback=action.progress)
	#await client.send_message(6537360, file)

async def youtube_download(url,update,message):
	await message.edit(f'downloading...')
    
	try:
		url = update.message.message
		youtube_path = os.path.join(download_path,'youtube')

		ydl_opts = { 'format': 'best', 'outtmpl': f'{youtube_path}/%(title)s.%(ext)s','cachedir':'False',"retries": 10 }

		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			info_dict = ydl.extract_info(url, download=False)
			file_name = ydl.prepare_filename(info_dict)
			total_downloads = 1
			if '_type' in info_dict and info_dict["_type"] == 'playlist':
				total_downloads = len(info_dict['entries'])
				#logger.info('info_dict :::::::::::: [{}][{}]'.format(info_dict["_type"],len(info_dict['entries'])))
				youtube_path = os.path.join(download_path,'youtube',info_dict['uploader'],info_dict['title'])
				ydl_opts = { 'format': 'best', 'outtmpl': f'{youtube_path}/%(title)s.%(ext)s','cachedir':'False','ignoreerrors': True, "retries": 10 }
				ydl_opts.update(ydl_opts)
			else:
				youtube_path = os.path.join(download_path,'youtube',info_dict['uploader'])
				ydl_opts = { 'format': 'best', 'outtmpl': f'{youtube_path}/%(title)s.%(ext)s','cachedir':'False','ignoreerrors': True, "retries": 10 }
				ydl_opts.update(ydl_opts)
		
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			logger.info(f'DOWNLOADING VIDEO YOUTUBE [{url}] [{file_name}]')
			await message.edit(f'downloading {total_downloads} videos...')
			res_youtube = ydl.download([url])

			if (res_youtube == False):
				filename = os.path.basename(file_name)
				logger.info(f'DOWNLOADED {total_downloads} VIDEO YOUTUBE [{file_name}] [{youtube_path}][{filename}]')
				await message.edit(f'downloaded {total_downloads} video')
			else:
				logger.info(f'ERROR: ONE OR MORE YOUTUBE VIDEOS NOT DOWNLOADED [{total_downloads}] [{url}] [{youtube_path}]')
				await message.edit(f'ERROR: one or more videos not downloaded') 
	except Exception as e:
		logger.info('ERROR: %s DOWNLOADING YT: %s' % (e.__class__.__name__, str(e)))
		logger.info(f'ERROR: Exception ONE OR MORE YOUTUBE VIDEOS NOT DOWNLOADED')

# Printing download progress
async def callback(current, total, file_path, message):
	value = (current / total) * 100
	format_float = "{:.2f}".format(value)
	int_value = int(float(format_float) // 1)
	try:
		if ((int_value != 100 ) and (int_value % 10 == 0)):
			task = loop.create_task(message.edit('Downloading... {}%'.format(format_float)))
	finally:
		current
 	#logger.info('Downloaded {} out of {} {}'.format(current,total,'bytes: {:.2%}'.format(current / total)))
	#await msg.edit("{} {}%".format(type_of, current * 100 / total))
	#logger.info('args {}'.format(file_path))
	#time.sleep(2)


async def worker(name):
	while True:
		# Esperando una unidad de trabajo.

		queue_item = await queue.get()
		update = queue_item[0]
		message = queue_item[1]
		FOLDER_TO_GROUP = queue_item[2] if queue_item[2] else ''

		real_id = get_peer_id(update.message.peer_id)
		CID , peer_type = resolve_id(real_id)

		# Comprobación de usuario
		if TG_AUTHORIZED_USER_ID and CID not in usuarios:
			logger.info('USUARIO: %s NO AUTORIZADO', CID)
			continue
		###
		file_path = tmp_path;
		file_name = 'FILENAME';
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
		await message.edit('Downloading...')
		logger.info('Downloading... ')
		mensaje = 'STARTING DOWNLOADING %s [%s] BY %s' % (time.strftime('%d/%m/%Y %H:%M:%S', time.localtime()), file_path , (CID))
		logger.info(mensaje)
		try:
			loop = asyncio.get_event_loop()
			task = loop.create_task(client.download_media(update.message, file_path, progress_callback=lambda x,y: callback(x,y,file_path,message)))
			download_result = await asyncio.wait_for(task, timeout = maximum_seconds_per_download)
			end_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())
			end_time_short = time.strftime('%H:%M', time.localtime())
			filename = os.path.split(download_result)[1]
			final_path = os.path.join(completed_path, filename)
			
			if FOLDER_TO_GROUP:
				final_path = os.path.join(FOLDER_TO_GROUP, filename)
				os.makedirs(FOLDER_TO_GROUP, exist_ok = True)
			else:
				# Ficheros .mp3 y .flac,
				if filename.endswith('.mp3') or filename.endswith('.flac'): final_path = os.path.join(download_path,"mp3", filename)
				# Ficheros .pdf y .cbr
				if filename.endswith('.pdf') or filename.endswith('.cbr'): final_path = os.path.join(download_path,"pdf", filename)
				# Ficheros .jpg
				if filename.endswith('.jpg'): 
					os.makedirs(os.path.join(download_path,'jpg'), exist_ok = True)
					final_path = os.path.join(download_path,"jpg", filename)
				# Ficheros .torrent
				if filename.endswith('.torrent'): final_path = os.path.join(download_path_torrent, filename)
			######
			logger.info("RENAME/MOVE [%s] [%s]" % (download_result, final_path) )
			os.makedirs(completed_path, exist_ok = True)
			shutil.move(download_result, final_path)
			######
			mensaje = 'DOWNLOAD FINISHED %s [%s]' % (end_time, file_name)
			logger.info(mensaje)
			await message.edit('Downloading finished:\n%s at %s' % (file_name,end_time_short))
		except asyncio.TimeoutError:
			print('[%s] Time exceeded %s' % (file_name, time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())))
			await message.edit('Error!')
			message = await update.reply('ERROR: Time exceeded downloading this file')
		except Exception as e:
			logger.critical(e)
			print('[EXCEPCION]: %s' % (str(e)))
			print('[%s] Excepcion %s' % (file_name, time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())))
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

		if update.message.media is not None and ( not TG_AUTHORIZED_USER_ID or CID in usuarios):
			if FOLDER_GROUP != update.message.date:
				logger.info("FOLDER_GROUP => [%s][%s][%s]" % (FOLDER_GROUP,update.message.date,temp_completed_path))
				temp_completed_path  = ''

		if update.message.media is not None and ( not TG_AUTHORIZED_USER_ID or CID in usuarios):
			file_name = 'NONAME';

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
		elif not TG_AUTHORIZED_USER_ID or CID in usuarios:
			if update.message.message == '/help':
				message = await update.reply(HELP) 
				await queue.put([update, message])
			elif update.message.message == '/version': 
				message = await update.reply(VERSION)
				await queue.put([update, message,temp_completed_path])
			elif update.message.message == '/alive': 
				message = await update.reply('Keep-Alive')
				await queue.put([update, message,temp_completed_path])
			elif update.message.message == '/me': 
				message = await update.reply('me: {}'.format(CID) )
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
					os.makedirs(os.path.join(download_path,'sendFiles'), exist_ok = True)
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
				#else:
				#	message = await update.reply('reply Keep-Alive: ' + update.message.message)
				#	await queue.put([update, message])
				#	logger.info("Eco del BOT :[%s]", update.message.message)
		else:
			logger.info('UNAUTHORIZED USER: %s ', CID)
			message = await update.reply('UNAUTHORIZED USER: %s \n add this ID to TG_AUTHORIZED_USER_ID' % CID)
	except Exception as e:
		message = await update.reply('ERROR: ' + str(e))
		logger.info('EXCEPTION USER: %s ', str(e))

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
	loop.run_until_complete(tg_send_message("Bot Torrent Download Started"))
	logger.info("%s" % VERSION)
	logger.info("********** START BOT_TORRENT_DOWNLOADER **********")



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
	
