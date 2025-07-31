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
                'extract_flat': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                is_playlist = 'entries' in info and info.get('_type') == 'playlist'
                playlist_count = len(info['entries']) if is_playlist else 0
                return info, is_playlist, playlist_count
        except Exception as e:
            self.logger.error(f"Error fetching video info for URL: {url}: {e}")
            return None, False, 0

    def download(self, url, download_type, progress_hook, is_playlist=False):
        """Downloads content from YouTube based on the specified type."""
        try:
            self.logger.info(f"Starting YouTube download for URL: {url} (Type: {download_type})")

            if download_type == 'video':
                path = self.config.YOUTUBE_VIDEO_FOLDER
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                    'noplaylist': not is_playlist,
                }
            elif download_type == 'audio':
                path = self.config.YOUTUBE_AUDIO_FOLDER
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                    'noplaylist': not is_playlist,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            else:
                self.logger.error(f"Invalid download type: {download_type}")
                return None, None

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                final_filename = None
                if not is_playlist:
                    final_filename = ydl.prepare_filename(info_dict)
            
            self.logger.info(f"Successfully finished YouTube download for URL: {url}")
            return info_dict, final_filename

        except Exception as e:
            self.logger.error(f"Error during YouTube download: {e}")
            return None, None
