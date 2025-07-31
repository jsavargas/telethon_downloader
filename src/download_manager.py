import os

class DownloadManager:
    def __init__(self, base_download_path, config_manager, logger, puid=None, pgid=None, torrent_path=None):
        self.base_download_path = base_download_path
        self.config_manager = config_manager
        self.logger = logger
        self.puid = puid
        self.pgid = pgid
        self.torrent_path = torrent_path

        try:
            # Default incompleted and completed directories
            self.default_incompleted_dir = os.path.join(self.base_download_path, "incompleted")
            self.default_completed_dir = os.path.join(self.base_download_path, "completed")
            
            self._ensure_dir_and_set_permissions(self.default_incompleted_dir)
            self._ensure_dir_and_set_permissions(self.default_completed_dir)

            # Temporary directory for in-progress downloads when a specific final path is given
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

    def get_download_dirs(self, extension, origin_group_id, channel_id, file_info):
        try:
            # 1. Check for keyword-based path
            keywords = self.config_manager.get_all_keywords()
            for keyword, path in keywords.items():
                if keyword.lower() in file_info.lower():
                    final_destination_dir = path
                    self.logger.info(f"Keyword '{keyword}' found in filename. Setting destination to {final_destination_dir}")
                    self._ensure_dir_and_set_permissions(final_destination_dir)
                    return self.temp_incompleted_dir, final_destination_dir

            # 2. Check for group-specific path (overrides keyword if both apply)
            group_path = self.config_manager.get_group_path(channel_id or origin_group_id) if (channel_id or origin_group_id) else None

            if group_path:
                final_destination_dir = group_path
                self.logger.info(f"Group path '{group_path}' found. Setting destination to {final_destination_dir}")
                self._ensure_dir_and_set_permissions(final_destination_dir)
                return self.temp_incompleted_dir, final_destination_dir

            # 3. Handle torrents (overrides group/keyword if it's a torrent)
            if extension.lower() == 'torrent' and self.torrent_path:
                final_destination_dir = self.torrent_path
                self.logger.info(f"Torrent detected. Setting destination to {final_destination_dir}")
                self._ensure_dir_and_set_permissions(final_destination_dir)
                return self.temp_incompleted_dir, final_destination_dir
            
            # 4. Check for extension-based path (overrides previous if it applies)
            configured_path = self.config_manager.get_download_path(extension)
            if configured_path:
                final_destination_dir = configured_path
                self.logger.info(f"Extension path '{configured_path}' found. Setting destination to {final_destination_dir}")
                self._ensure_dir_and_set_permissions(final_destination_dir)
                return self.temp_incompleted_dir, final_destination_dir


            # Ensure the final destination directory exists and has correct permissions
            self._ensure_dir_and_set_permissions(self.default_completed_dir)

            return self.default_incompleted_dir, self.default_completed_dir
        except Exception as e:
            self.logger.error(f"Error getting download directories for extension {extension}, origin {origin_group_id}, and file {file_info}: {e}")
            return self.default_incompleted_dir, self.default_completed_dir # Fallback to default

    def move_to_completed(self, downloaded_file_path, target_completed_dir):
        try:
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