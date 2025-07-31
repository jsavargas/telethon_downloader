import yt_dlp
import os
from logger_config import LoggerConfig

class YouTubeDownloader:
    def __init__(self, config):
        self.config = config
        self.logger = LoggerConfig()

    def get_video_info(self, url):
        """Gets information about a YouTube URL without downloading."""
        try:
            self.logger.info(f"Fetching video info for URL: {url}")
            ydl_opts = {
                'extract_flat': True,  # Don't get info for each video in a playlist
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                is_playlist = 'entries' in info and info.get('_type') == 'playlist'
                playlist_count = len(info['entries']) if is_playlist else 0
                self.logger.info(f"Successfully fetched video info for URL: {url}")
                return info, is_playlist, playlist_count
        except Exception as e:
            self.logger.error(f"Error fetching video info for URL: {url}: {e}")
            return None, False, 0

    def download_video(self, url, download_path, progress_hook, is_playlist=False):
        """Downloads a video or playlist, returning the info and final filename."""
        try:
            self.logger.info(f"Starting download for URL: {url} to path: {download_path}")

            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'noplaylist': not is_playlist,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                
                final_filename = None
                if not is_playlist:
                    # For single videos, get the exact final path
                    final_filename = ydl.prepare_filename(info_dict)

            self.logger.info(f"Successfully finished download for URL: {url}")
            return info_dict, final_filename

        except Exception as e:
            self.logger.error(f"Error downloading video from URL: {url}: {e}")
            return None, None