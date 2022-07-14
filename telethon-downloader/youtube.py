import os
import shutil
import time
#import youtube_dl
import subprocess
import aiofiles
import re



from logger import logger
from env import YOUTUBE_FORMAT, TG_DOWNLOAD_PATH, PATH_YOUTUBE



def execute(command):
	logger.info(f'youtube_download: {command}')
	process = subprocess.Popen(command, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = ''
	for line in iter(process.stdout.readline, ''):
		output += line
	process.wait()
	exit_code = process.returncode

	if exit_code == 0:
		return output
	else:
		raise Exception(command, exit_code, output)



async def youtube_download(url,update,message):
	await message.edit(f'downloading...')
    
	try:
		url = update.message.message
		youtube_path = PATH_YOUTUBE
		
		youtubedl_args_format = ''

		if not os.path.exists('/config/args.conf'):
			shutil.copyfile('/config.default/args.conf', '/config/args.conf')

		async with aiofiles.open('/config/args.conf') as f:
			if re.search(r'(--format |-f )', await f.read(), flags=re.I | re.MULTILINE) is not None:
				youtubedl_args_format = ''
			else:
				with open('/config.default/format') as default_format:
					youtubedl_args_format = f'--format "{str(default_format.read()).strip()}"'


		#ydl_opts = { 'format': YOUTUBE_FORMAT, 'outtmpl': f'{youtube_path}/%(title)s.%(ext)s','cachedir':'False',"retries": 10 }

		youtubedl_binary = 'yt-dlp'
		execute(f'{youtubedl_binary} \'{url}\' --no-playlist-reverse --playlist-end \'-1\' --config-location \'/config/args.conf\' {youtubedl_args_format}')


		end_time_short = time.strftime('%H:%M', time.localtime())
		await message.edit(f'Downloading finished {url} video at {end_time_short}')

		return True

	except Exception as e:
		logger.info('ERROR: %s DOWNLOADING YT: %s' % (e.__class__.__name__, str(e)))
		logger.info(f'ERROR: Exception ONE OR MORE YOUTUBE VIDEOS NOT DOWNLOADED')

		return False
