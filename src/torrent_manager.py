import os
import shutil
from qbittorrentapi import Client as qbt_client
from logger_config import LoggerConfig

class TorrentManager:
    def __init__(self, env_config, logger):
        self.env_config = env_config
        self.logger = logger
        self.qbt_client = None

        if self.env_config.TORRENT_MODE == 'qbt_api':
            self._init_qbt_client()

    def _init_qbt_client(self):
        try:
            self.qbt_client = qbt_client(
                host=self.env_config.QBT_HOST,
                port=self.env_config.QBT_PORT,
                username=self.env_config.QBT_USERNAME,
                password=self.env_config.QBT_PASSWORD
            )
            self.qbt_client.auth_log_in()
            self.logger.info("Successfully connected to qBittorrent API using qbittorrentapi.")
        except Exception as e:
            self.logger.error(f"Error connecting to qBittorrent API: {e}")
            self.qbt_client = None

    def add_torrent(self, torrent_file_path, download_path=None, category=None):
        if self.env_config.TORRENT_MODE == 'qbt_api':
            return self._add_torrent_qbt_api(torrent_file_path, download_path, category)
        elif self.env_config.TORRENT_MODE == 'watch':
            return self._add_torrent_watch_folder(torrent_file_path)
        else:
            self.logger.error(f"Unknown TORRENT_MODE: {self.env_config.TORRENT_MODE}")
            return None

    def _add_torrent_qbt_api(self, torrent_file_path, download_path, category=None):
        if not self.qbt_client:
            self.logger.error("qBittorrent client not initialized. Cannot add torrent.")
            return None
        try:
            with open(torrent_file_path, 'rb') as f:
                self.qbt_client.torrents_add(torrent_files=f.read(), category=category)
            self.logger.info(f"Torrent {os.path.basename(torrent_file_path)} added via qBittorrent API with category '{category}'.")
            new_path = os.path.join(self.env_config.BASE_DOWNLOAD_PATH, "torrents", os.path.basename(torrent_file_path))
            return new_path
        except Exception as e:
            self.logger.error(f"Error adding torrent via qBittorrent API: {e}")
            return None

    def _add_torrent_watch_folder(self, torrent_file_path):
        watch_folder = self.env_config.DOWNLOAD_PATH_TORRENTS
        try:
            shutil.move(torrent_file_path, watch_folder)
            self.logger.info(f"Torrent {os.path.basename(torrent_file_path)} moved to watch folder: {watch_folder}")
            return torrent_file_path
        except Exception as e:
            self.logger.error(f"Error moving torrent to watch folder: {e}")
            return None

    def get_categories(self):
        if not self.qbt_client:
            self.logger.error("qBittorrent client not initialized. Cannot get categories.")
            return []
        try:
            categories = self.qbt_client.torrents_categories()
            return list(categories)
        except Exception as e:
            self.logger.error(f"Error getting categories from qBittorrent API: {e}")
            return []