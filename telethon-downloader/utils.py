import os
import re
import configparser
from typing import List, Tuple

from logger import logger
from env import PATH_COMPLETED, TG_FOLDER_BY_AUTHORIZED, TG_DOWNLOAD_PATH_TORRENTS, \
	TG_AUTHORIZED_USER_ID, PATH_CONFIG

def splash() -> None:
	""" Displays splash screen """
	logger.info('''
----------------------------------------------
   _
  (_)___  __ ___   ____ _ _ __ __ _  __ _ ___
  | / __|/ _` \ \ / / _` | '__/ _` |/ _` / __|
  | \__ \ (_| |\ V / (_| | | | (_| | (_| \__ \\
 _/ |___/\__,_| \_/ \__,_|_|  \__, |\__,_|___/
|__/                          |___/

----------------------------------------------
    
----------------------------------------------
 _       _      _   _
| |_ ___| | ___| |_| |__   ___  _ __
| __/ _ \ |/ _ \ __| '_ \ / _ \| '_ \\
| ||  __/ |  __/ |_| | | | (_) | | | |
 \__\___|_|\___|\__|_| |_|\___/|_| |_|

     _                     _                 _
  __| | _____      ___ __ | | ___   __ _  __| | ___ _ __
 / _` |/ _ \ \ /\ / / '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|
| (_| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __/ |
 \__,_|\___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|


----------------------------------------------
	''')


def create_directory(download_path: str) -> None:
	try:
		os.makedirs(download_path, exist_ok=True)
	except Exception as e:
		logger.info(f'create_directory Exception : {download_path} [{e}]')



def getDownloadPath(filename,CID):
	config = read_config_file()

	download_path = PATH_COMPLETED
	folderFlag=False

	if (TG_FOLDER_BY_AUTHORIZED==True or TG_FOLDER_BY_AUTHORIZED == 'True' ) and (CID in config['FOLDER_BY_AUTHORIZED']):
		FOLDER_BY_AUTHORIZED = config['FOLDER_BY_AUTHORIZED']
		for AUTHORIZED in FOLDER_BY_AUTHORIZED:
			if AUTHORIZED == CID:
				download_path = FOLDER_BY_AUTHORIZED[AUTHORIZED]
				folderFlag=True
				break

	if not folderFlag:
		REGEX_PATH = config['REGEX_PATH']
		for regex in REGEX_PATH:
			m = re.search('/(.*)/(.*)', regex)
			if m :
				if m.group(2) == 'i':
					result = re.search(m.group(1), filename,re.I)
					if result :
						if result.group(0):
							logger.info(f'REGEX_PATH :::: {regex} 1:[{result.group(0)}] ')
							download_path = os.path.join(REGEX_PATH[regex])
							folderFlag=True
							break
				else:	
					result = re.search(m.group(1), filename)
					if result:
						if result.group(0):
							download_path = os.path.join(REGEX_PATH[regex])
							folderFlag=True
							break
	logger.info(f'getDownloadPath : {download_path}')

	if not folderFlag:
		DEFAULT_PATH = config['DEFAULT_PATH']
		for ext in DEFAULT_PATH:
			if filename.endswith(ext):
				download_path = os.path.join(download_path,ext)
				download_path = DEFAULT_PATH[ext] #os.path.join(download_path,ext)
				folderFlag=True
				break

	if filename.endswith('.torrent'): download_path = TG_DOWNLOAD_PATH_TORRENTS

	complete_path = os.path.join(download_path,filename)
	#create_directory(download_path)
	#os.chmod(download_path, 0o777)
	logger.info(f'getDownloadPath getDownloadPath  : {download_path}')

	return download_path, complete_path


def getUsers() -> List[str]:
	""" Returns a list of inputted strings """
	inputs = []
	if TG_AUTHORIZED_USER_ID==False:
		return False, inputs
	elif TG_AUTHORIZED_USER_ID.strip() == '':
		return False, inputs
	else:		
		inputs = list(map(int, TG_AUTHORIZED_USER_ID.strip().replace(" ", "").replace('-100', '').split(',')))
		return True, inputs


def split_input(input) -> List[str]:
	""" Returns a list of inputted strings """
	inputs = []
	if TG_AUTHORIZED_USER_ID.strip() == '':
		return inputs
	else:		
		inputs = list(map(str, input.replace(" ", "").split(','))) 
		return inputs


def config_file():
	config = configparser.ConfigParser()
	if not os.path.exists(PATH_CONFIG):
		logger.info(f'CREATE DEFAULT CONFIG FILE : {PATH_CONFIG}')
	
		config.read(PATH_CONFIG)
			
		config['DEFAULT_PATH'] = {}
		config['DEFAULT_PATH']['pdf'] = '/download/pdf'
		config['DEFAULT_PATH']['cbr'] = '/download/pdf'
		config['DEFAULT_PATH']['mp3'] = '/download/mp3'
		config['DEFAULT_PATH']['flac'] = '/download/mp3'
		config['DEFAULT_PATH']['jpg'] = '/download/jpg'
		config['DEFAULT_PATH']['mp4'] = '/download/mp4'

		config['REGEX_PATH'] = {}
		config['REGEX_PATH']['/example/i'] = '/download/example'

		config['FOLDER_BY_AUTHORIZED'] = {}

		AUTHORIZED_USER, usuarios = getUsers()

		for usuario in usuarios:
			config['FOLDER_BY_AUTHORIZED'][f"{usuario}"] = '/download/{}'.format(f"{usuario}")

		with open(PATH_CONFIG, 'w') as configfile:    # save
			config.write(configfile)
		return config
	else:
		config.read(PATH_CONFIG)
		if not 'REGEX_PATH' in config:
			config['REGEX_PATH'] = {}
			config['REGEX_PATH']['/example.*example/i'] = '/download/example'
			with open(PATH_CONFIG, 'w') as configfile:    # save
				config.write(configfile)

		logger.info(f'READ CONFIG FILE : {PATH_CONFIG}')

		return config


def read_config_file():
	config = configparser.ConfigParser()
	config.read(PATH_CONFIG)
	return config

