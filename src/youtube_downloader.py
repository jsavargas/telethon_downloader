import yt_dlp
import os
from logger_config import LoggerConfig

class YouTubeDownloader:
    def __init__(self, config):
        self.config = config
        self.download_path = self.config.YOUTUBE_VIDEO_FOLDER
        self.video_format = self.config.YOUTUBE_FORMAT_VIDEO
        self.logger = LoggerConfig()

    def get_video_info(self, url):
        try:
            self.logger.info(f"Fetching video info for URL: {url}")
            ydl_opts = {'extract_flat': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                is_playlist = 'entries' in info and info.get('_type') == 'playlist'
                playlist_count = len(info['entries']) if is_playlist else 0
                self.logger.info(f"Successfully fetched video info for URL: {url}")
                return info, is_playlist, playlist_count
        except Exception as e:
            self.logger.error(f"Error fetching video info for URL: {url}: {e}")
            return None, False, 0

    def download_video(self, url, download_path=None, playlist=False, progress_callback=None):
        download_info = {}
        try:
            path = download_path or self.download_path
            self.logger.info(f"Starting download for URL: {url} to path: {path}")
            
            def progress_hook(d):
                if d['status'] == 'downloading' and progress_callback:
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    if total_bytes:
                        progress_callback(d['downloaded_bytes'], total_bytes)
                elif d['status'] == 'finished':
                    download_info['filename'] = d.get('filename')
                    download_info['total_bytes'] = d.get('total_bytes')

            ydl_opts = {
                'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                'noplaylist': not playlist,
                'progress_hooks': [progress_hook],
                'format': self.video_format,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.logger.info(f"Successfully downloaded video from URL: {url} to path: {path}")
            return download_info
        except Exception as e:
            self.logger.error(f"Error downloading video from URL: {url}: {e}")
            return None