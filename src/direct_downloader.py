import os
import asyncio
import time
import aiohttp

class DirectDownloader:
    def __init__(self, env_config, logger, download_manager, finalize_download_processing_callback):
        self.env_config = env_config
        self.logger = logger
        self.download_manager = download_manager
        self._finalize_download_processing = finalize_download_processing_callback

    async def download_file(self, event, url, initial_message):
        try:
            file_name = url.split('/')[-1]
            if '?' in file_name:
                file_name = file_name.split('?')[0]
            
            file_extension = os.path.splitext(file_name)[1].lstrip('.') # Get extension without the dot

            # Use DownloadManager to get the appropriate download directories
            target_download_dir, final_destination_dir = self.download_manager.get_download_dirs(
                file_extension, 
                event.sender_id, # Assuming sender_id can be used as origin_group_id
                None, # No channel_id for direct links
                file_name
            )
            os.makedirs(target_download_dir, exist_ok=True)
            download_path = os.path.join(target_download_dir, file_name)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    start_time = time.time()
                    last_update_time = time.time()

                    with open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            current_time = time.time()
                            if current_time - last_update_time > 2: # Update every 2 seconds
                                speed = downloaded_size / (current_time - start_time) if (current_time - start_time) > 0 else 0
                                progress_text = f"Downloading: {file_name}\n{downloaded_size / (1024*1024):.2f}MB / {total_size / (1024*1024):.2f}MB ({downloaded_size/total_size:.1%})\nSpeed: {speed / (1024*1024):.2f}MB/s"
                                await initial_message.edit(progress_text)
                                last_update_time = current_time
            
            end_time = time.time()
            await self._finalize_download_processing(initial_message, event.message, file_name, final_destination_dir, start_time, end_time, total_size, event.sender_id, event.sender_id, None, file_extension, download_path)

        except Exception as e:
            self.logger.error(f"Error downloading direct link: {e}")
            await initial_message.edit(f"Error downloading link: {e}")
