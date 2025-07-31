import yt_dlp
import os
from logger_config import LoggerConfig

class YouTubeDownloader:
    def __init__(self, download_path='.'):
        self.download_path = download_path
        self.logger = LoggerConfig()

    def get_video_info(self, url):
        try:
            self.logger.info(f"Fetching video info for URL: {url}")
            ydl_opts = {'extract_flat': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                is_playlist = 'entries' in info and info.get('_type') == 'playlist'
                self.logger.info(f"Successfully fetched video info for URL: {url}")
                return info, is_playlist
        except Exception as e:
            self.logger.error(f"Error fetching video info for URL: {url}: {e}")
            return None, False

    def download_video(self, url, download_path=None, playlist=False):
        try:
            path = download_path or self.download_path
            self.logger.info(f"Starting download for URL: {url} to path: {path}")
            ydl_opts = {
                'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                'noplaylist': not playlist,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.logger.info(f"Successfully downloaded video from URL: {url} to path: {path}")
        except Exception as e:
            self.logger.error(f"Error downloading video from URL: {url}: {e}")
