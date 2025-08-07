import re
import os
import shutil
from torrent_manager import TorrentManager

class DownloadManager:
    def __init__(self, base_download_path, config_manager, logger, env_config, puid=None, pgid=None, torrent_path=None):
        self.base_download_path = base_download_path
        self.config_manager = config_manager
        self.logger = logger
        self.env_config = env_config
        self.puid = puid
        self.pgid = pgid
        self.torrent_path = torrent_path

        self.torrent_manager = TorrentManager(env_config, logger)

        try:
            self.default_incompleted_dir = os.path.join(self.base_download_path, "incompleted")
            self.default_completed_dir = os.path.join(self.base_download_path, "completed")
            
            self._ensure_dir_and_set_permissions(self.default_incompleted_dir)
            self._ensure_dir_and_set_permissions(self.default_completed_dir)

            self.temp_incompleted_dir = self.default_incompleted_dir
            self._ensure_dir_and_set_permissions(self.temp_incompleted_dir)
        except Exception as e:
            self.logger.error(f"Error during DownloadManager initialization: {e}")

    def _apply_permissions_and_ownership(self, path):
        try:
            if self.puid is not None and self.pgid is not None:
                try:
                    os.chown(path, int(self.puid), int(self.pgid))
                    self.logger.info(f"Changed ownership of directory {path} to {int(self.puid)}:{int(self.pgid)}")
                except Exception as e:
                    self.logger.error(f"Error changing ownership of directory {path}: {e}")
            try:
                os.chmod(path, 0o755) # Set permissions for directories
                self.logger.info(f"Changed permissions of directory {path} to 0o755")
            except Exception as e:
                self.logger.error(f"Error changing permissions of directory {path}: {e}")
        except Exception as e:
            self.logger.error(f"Unhandled exception in _apply_permissions_and_ownership for {path}: {e}")

    def _ensure_dir_and_set_permissions(self, path):
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                self._apply_permissions_and_ownership(path)
        except Exception as e:
            self.logger.error(f"Error ensuring directory {path} exists and setting permissions: {e}")

    def _get_regex_destination(self, file_info):
        regex_paths = self.config_manager.get_all_regex_paths()
        for pattern, path in regex_paths.items():
            try:
                # Check for case-insensitive flag 'i'
                flags = 0
                if pattern.endswith('/i'):
                    pattern = pattern[:-1]  
                    flags = re.IGNORECASE
                
                # Remove enclosing slashes /.../
                if pattern.startswith('/') and pattern.endswith('/'):
                    pattern = pattern[1:-1]

                if re.search(pattern, file_info, flags):
                    self.logger.info(f"Regex pattern '{pattern}' matched in filename. Proposed destination: {path}")
                    return path
            except re.error as e:
                self.logger.error(f"Invalid regex pattern '{pattern}': {e}")
        return None

    def _get_keyword_destination(self, file_info):
        keywords = self.config_manager.get_all_keywords()
        for keyword, path in keywords.items():
            if keyword.lower() in file_info.lower():
                self.logger.info(f"Keyword '{keyword}' found in filename. Proposed destination: {path}")
                return path
        return None

    def _get_group_destination(self, origin_group_id, channel_id):
        group_path = None
        if channel_id:
            group_path = self.config_manager.get_group_path(channel_id)
        elif origin_group_id:
            group_path = self.config_manager.get_group_path(origin_group_id)
        if group_path:
            self.logger.info(f"Group path '{group_path}' found. Proposed destination: {group_path}")
        return group_path

    def _get_torrent_destination(self, extension):

        if extension.lower() == 'torrent' and self.env_config.TORRENT_MODE != 'watch':
            return os.path.join(self.env_config.BASE_DOWNLOAD_PATH, "torrents")
        if extension.lower() == 'torrent' and self.torrent_path:
            self.logger.info(f"Torrent detected. Proposed destination: {self.torrent_path}")
            return self.torrent_path
        return None

    def _get_extension_destination(self, extension):
        configured_path = self.config_manager.get_download_path(extension)
        if configured_path:
            self.logger.info(f"Extension path '{configured_path}' found. Proposed destination: {configured_path}")
        return configured_path

    def get_download_dirs(self, extension, origin_group_id, channel_id, file_info):
        try:
            final_destination_dir = self.default_completed_dir
            self.logger.info(f"get_download_dirs default_completed_dir: {final_destination_dir}")

            # Order of precedence: Torrent > Regex > Keyword > Group > Extension > Default
            torrent_dest = self._get_torrent_destination(extension)
            regex_dest = self._get_regex_destination(file_info)
            keyword_dest = self._get_keyword_destination(file_info)
            group_dest = self._get_group_destination(origin_group_id, channel_id)
            extension_dest = self._get_extension_destination(extension)

            if torrent_dest:
                final_destination_dir = torrent_dest
            elif regex_dest:
                final_destination_dir = regex_dest
            elif keyword_dest:
                final_destination_dir = keyword_dest
            elif group_dest:
                final_destination_dir = group_dest
            elif extension_dest:
                final_destination_dir = extension_dest

            self.logger.info(f"get_download_dirs final_destination_dir: {final_destination_dir}")
            
            self._ensure_dir_and_set_permissions(final_destination_dir)

            target_incompleted_dir = self.temp_incompleted_dir

            return target_incompleted_dir, final_destination_dir
        except Exception as e:
            self.logger.error(f"Error getting download directories for extension {extension}, origin {origin_group_id}, and file {file_info}: {e}")
            return self.default_incompleted_dir, self.default_completed_dir # Fallback to default

    def move_to_completed(self, downloaded_file_path, target_completed_dir, category=None):
        try:
            if downloaded_file_path.lower().endswith('.torrent'):
                self.logger.info(f"Detected torrent file: {downloaded_file_path}. Handing to TorrentManager.")
                processed_torrent_path = self.torrent_manager.add_torrent(downloaded_file_path, target_completed_dir, category)
                if processed_torrent_path:
                    self.logger.info(f"torrent file processed_torrent_path {processed_torrent_path} via TorrentManager.")
                    self.logger.info(f"torrent file downloaded_file_path {downloaded_file_path} via TorrentManager.")
                    self.logger.info(f"torrent file target_completed_dir {target_completed_dir} via TorrentManager.")
                    os.rename(downloaded_file_path, processed_torrent_path)
                    return processed_torrent_path
                else:
                    self.logger.error(f"Failed to add torrent {downloaded_file_path} via TorrentManager.")
                    return None # Indicate failure to the caller

            final_file_path = os.path.join(target_completed_dir, os.path.basename(downloaded_file_path))
            os.rename(downloaded_file_path, final_file_path)
            
            # Set permissions and ownership
            if self.puid is not None and self.pgid is not None:
                try:
                    os.chown(final_file_path, int(self.puid), int(self.pgid))
                    self.logger.info(f"Changed ownership of file {final_file_path} to {int(self.puid)}:{int(self.pgid)}")
                except Exception as e:
                    self.logger.error(f"Error changing ownership of {final_file_path}: {e}")
            try:
                os.chmod(final_file_path, 0o644) # Set read/write for owner, read-only for others
                self.logger.info(f"Changed permissions of file {final_file_path} to 0o644")
                return final_file_path
            except Exception as e:
                self.logger.error(f"Error changing permissions of {final_file_path}: {e}")
                return final_file_path # Return path even if permissions fail
        except Exception as e:
            self.logger.error(f"Error in move_to_completed for {downloaded_file_path}: {e}")
            return downloaded_file_path # Return original path if move fails

    def move_file(self, file_path, destination_dir):
        try:
            file_name = os.path.basename(file_path)
            new_file_path = os.path.join(destination_dir, file_name)
            os.rename(file_path, new_file_path)
            
            # Set permissions and ownership
            if self.puid is not None and self.pgid is not None:
                try:
                    os.chown(new_file_path, int(self.puid), int(self.pgid))
                    self.logger.info(f"Changed ownership of file {new_file_path} to {int(self.puid)}:{int(self.pgid)}")
                except Exception as e:
                    self.logger.error(f"Error changing ownership of {new_file_path}: {e}")
            try:
                os.chmod(new_file_path, 0o644) # Set read/write for owner, read-only for others
                self.logger.info(f"Changed permissions of file {new_file_path} to 0o644")
            except Exception as e:
                self.logger.error(f"Error changing permissions of {new_file_path}: {e}")

            self.logger.info(f"File moved successfully to {new_file_path}")
            return new_file_path
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            return None

    def add_magnet_link_with_category(self, magnet_uri, category=None):
        if self.env_config.TORRENT_MODE == 'qbittorrent':
            return self.torrent_manager._add_magnet_qbt_api(magnet_uri, category)
        else:
            self.logger.error(f"Magnet links can only be added with TORRENT_MODE set to 'qbittorrent'. Current mode: {self.env_config.TORRENT_MODE}")
            return None