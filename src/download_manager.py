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
            
            os.makedirs(self.default_incompleted_dir, exist_ok=True)
            self._apply_permissions_and_ownership(self.default_incompleted_dir)
            os.makedirs(self.default_completed_dir, exist_ok=True)
            self._apply_permissions_and_ownership(self.default_completed_dir)

            # Temporary directory for in-progress downloads when a specific final path is given
            self.temp_incompleted_dir = os.path.join(self.base_download_path, "temp_incompleted")
            os.makedirs(self.temp_incompleted_dir, exist_ok=True)
            self._apply_permissions_and_ownership(self.temp_incompleted_dir)
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

    def get_download_dirs(self, extension, origin_group_id, channel_id):
        try:
            # Check for group-specific path first
            group_path = None
            if channel_id:
                group_path = self.config_manager.get_group_path(channel_id)
            elif origin_group_id:
                group_path = self.config_manager.get_group_path(origin_group_id)

            if group_path:
                target_incompleted_dir = self.temp_incompleted_dir
                target_completed_dir = group_path
                
                # Only create and apply permissions if the directory doesn't exist
                if not os.path.exists(target_completed_dir):
                    os.makedirs(target_completed_dir, exist_ok=True)
                    self._apply_permissions_and_ownership(target_completed_dir)

                return target_incompleted_dir, target_completed_dir

            # Handle torrents
            if extension.lower() == 'torrent' and self.torrent_path:
                os.makedirs(self.torrent_path, exist_ok=True)
                self._apply_permissions_and_ownership(self.torrent_path)
                return self.torrent_path, self.torrent_path # Download and complete in the same torrent path

            configured_path = self.config_manager.get_download_path(extension)
            if configured_path:
                # If a specific path is configured, use it as the final destination
                # and use a temporary incompleted directory
                target_incompleted_dir = self.temp_incompleted_dir
                target_completed_dir = configured_path
                
                # Only create and apply permissions if the directory doesn't exist
                if not os.path.exists(target_completed_dir):
                    os.makedirs(target_completed_dir, exist_ok=True)
                    self._apply_permissions_and_ownership(target_completed_dir)

                return target_incompleted_dir, target_completed_dir
            else:
                # Otherwise, use the default incompleted/completed structure
                return self.default_incompleted_dir, self.default_completed_dir
        except Exception as e:
            self.logger.error(f"Error getting download directories for extension {extension} and origin {origin_group_id}: {e}")
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
            except Exception as e:
                self.logger.error(f"Error changing permissions of {final_file_path}: {e}")

            return final_file_path
        except Exception as e:
            self.logger.error(f"Error moving file {downloaded_file_path} to {target_completed_dir}: {e}")
            return downloaded_file_path # Return original path if move fails
