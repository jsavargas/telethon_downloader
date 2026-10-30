import asyncio
import os
import re
import time
from telethon import events, Button
from download_summary import DownloadSummary


class YouTubeHandler:
    def __init__(self, bot, youtube_downloader, env_config, logger):
        self.bot = bot
        self.youtube_downloader = youtube_downloader
        self.env_config = env_config
        self.logger = logger
        self.active_youtube_prompts = {}

    async def handle_youtube_link(self, event):
        try:
            self.logger.info(f"YouTube link detected in message ID: {event.message.id}")
            processing_message = await event.reply("Processing YouTube link...")

            match = re.search(r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+", event.message.text)
            if not match:
                await processing_message.edit("Could not find a valid YouTube URL.")
                return

            url = match.group(0).rstrip(')')
            info, is_playlist, playlist_count = await asyncio.get_event_loop().run_in_executor(
                None, self.youtube_downloader.get_video_info, url
            )

            if info is None:
                await processing_message.edit("Could not process the YouTube URL.")
                return

            if is_playlist:
                buttons = [
                    [Button.inline("Download First", data=f"yt_playlist_first_{event.message.id}".encode('utf-8'))],
                    [Button.inline(f"Download All ({playlist_count})", data=f"yt_playlist_all_{event.message.id}".encode('utf-8'))]
                ]
                await processing_message.edit(
                    f"This is a playlist with {playlist_count} videos. What would you like to do?",
                    buttons=buttons
                )
            else:
                buttons = [
                    [Button.inline("Video", data=f"yt_single_video_{event.message.id}".encode('utf-8'))],
                    [Button.inline("Audio", data=f"yt_single_audio_{event.message.id}".encode('utf-8'))],
                    [Button.inline("Both", data=f"yt_single_both_{event.message.id}".encode('utf-8'))]
                ]
                await processing_message.edit("What format would you like to download?", buttons=buttons)

            asyncio.create_task(self._start_timeout_task(processing_message, url))

        except Exception as e:
            self.logger.error(f"Error in handle_youtube_link: {e}")
            await event.reply(f"An error occurred: {e}")

    async def handle_youtube_choice(self, event):
        prompt_message = await event.get_message()
        if prompt_message.id in self.active_youtube_prompts:
            del self.active_youtube_prompts[prompt_message.id]
        else:
            await event.answer("This action has expired.")
            return

        try:
            data = event.data.decode('utf-8')
            self.logger.info(f"YouTube choice callback received: {data}")

            parts = data.split('_')
            source_type, download_scope, original_message_id_str = parts[1], parts[2], parts[3]

            original_message = await self.bot.get_messages(event.chat_id, ids=int(original_message_id_str))
            if not original_message or not original_message.text:
                await event.edit("Could not find the original message.")
                return

            match = re.search(r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+", original_message.text)
            if not match:
                await event.edit("Could not find a URL in the original message.")
                return
            url = match.group(0).rstrip(')')

            if source_type == 'playlist':
                is_playlist = (download_scope == 'all')
                buttons = [
                    [Button.inline("Video", data=f"yt_final_video_{is_playlist}_{original_message.id}".encode('utf-8'))],
                    [Button.inline("Audio", data=f"yt_final_audio_{is_playlist}_{original_message.id}".encode('utf-8'))],
                    [Button.inline("Both", data=f"yt_final_both_{is_playlist}_{original_message.id}".encode('utf-8'))]
                ]
                await event.edit("What format would you like to download?", buttons=buttons)
                asyncio.create_task(self._start_timeout_task(prompt_message, url))

            elif source_type == 'final' or source_type == 'single':
                download_type = download_scope
                is_playlist = (parts[3] == 'True') if source_type == 'final' else False
                await event.edit("Selection received. Starting download...")
                await self._perform_youtube_download(event, url, download_type, is_playlist)

        except Exception as e:
            self.logger.error(f"Error in handle_youtube_choice: {e}")
            await event.answer(f"An error occurred: {e}")

    async def _start_timeout_task(self, prompt_message, url):
        prompt_id = prompt_message.id
        self.active_youtube_prompts[prompt_id] = {"url": url, "event": prompt_message}
        await asyncio.sleep(self.env_config.YOUTUBE_TIMEOUT_OPTION)
        if prompt_id in self.active_youtube_prompts:
            await self._handle_youtube_timeout(prompt_id)

    async def _handle_youtube_timeout(self, prompt_id):
        self.logger.info(f"YouTube prompt {prompt_id} timed out.")
        prompt_context = self.active_youtube_prompts.pop(prompt_id, None)
        if not prompt_context:
            return
        event = prompt_context["event"]
        url = prompt_context["url"]
        await event.edit(f"Timed out. Defaulting to first video, {self.env_config.YOUTUBE_DEFAULT_DOWNLOAD} format.")
        await self._perform_youtube_download(event, url, self.env_config.YOUTUBE_DEFAULT_DOWNLOAD, is_playlist=False)

    async def _perform_youtube_download(self, event, url, download_type, is_playlist):
        if isinstance(event, events.CallbackQuery.Event):
            message_to_edit = await event.get_message()
        else:
            message_to_edit = event

        main_loop = asyncio.get_event_loop()

        async def download_and_summarize(dl_type):
            start_time = time.time()
            last_update_time = 0

            def _progress_hook(d):
                nonlocal last_update_time
                if d['status'] == 'downloading':
                    current_time = time.time()
                    if current_time - last_update_time < 2:
                        return
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    if not total_bytes:
                        return
                    downloaded_bytes = d['downloaded_bytes']
                    percentage = (downloaded_bytes / total_bytes) * 100
                    speed = d.get('speed') or 0
                    eta = d.get('eta') or 0
                    video_title = d.get('info_dict', {}).get('title', 'Unknown')
                    progress_title = f"Downloading {dl_type.capitalize()}s" if is_playlist else f"Downloading {dl_type.capitalize()}"
                    progress_text = (
                        f"**{progress_title}:** {video_title}\n"
                        f"{percentage:.1f}% of {total_bytes/(1024*1024):.2f}MB "
                        f"at {speed/(1024*1024):.2f}MB/s, ETA: {eta:.0f}s"
                    )
                    asyncio.run_coroutine_threadsafe(
                        message_to_edit.edit(progress_text, buttons=None), main_loop
                    )
                    last_update_time = current_time

            info_dict, final_filename = await main_loop.run_in_executor(
                None, self.youtube_downloader.download, url, dl_type, _progress_hook, is_playlist
            )
            end_time = time.time()

            if not info_dict:
                return f"Could not download {dl_type}. Check logs."

            if is_playlist:
                folder = self.env_config.YOUTUBE_VIDEO_FOLDER if dl_type == 'video' else self.env_config.YOUTUBE_AUDIO_FOLDER
                summary = DownloadSummary(message_to_edit, info_dict.get('title', 'N/A'), folder, start_time, end_time, 0, None, None, None, status='completed', download_type='youtube')
            else:
                total_bytes = info_dict.get('filesize') or info_dict.get('filesize_approx') or 0
                summary = DownloadSummary(message_to_edit, os.path.basename(final_filename), os.path.dirname(final_filename), start_time, end_time, total_bytes, None, None, None, status='completed', download_type='youtube')
            return summary.generate_summary()

        try:
            if download_type == 'both':
                await message_to_edit.edit("Starting video download...", buttons=None)
                video_summary = await download_and_summarize('video')
                await message_to_edit.edit(video_summary + "\n\nStarting audio download...", buttons=None)
                audio_summary = await download_and_summarize('audio')
                await message_to_edit.edit(video_summary + "\n" + audio_summary, buttons=None)
            else:
                summary = await download_and_summarize(download_type)
                await message_to_edit.edit(summary, buttons=None)

        except Exception as e:
            self.logger.error(f"Error in _perform_youtube_download: {e}")
            await message_to_edit.edit(f"An error occurred: {e}")
