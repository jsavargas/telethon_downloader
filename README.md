# Telethon Downloader

[![](https://badgen.net/badge/icon/github?icon=github&label)](https://github.com/jsavargas/telethon_downloader)
[![](https://badgen.net/badge/icon/docker?icon=docker&label)](https://hub.docker.com/r/jsavargas/telethon_downloader)
[![Docker Pulls](https://badgen.net/docker/pulls/jsavargas/telethon_downloader?icon=docker&label=pulls)](https://hub.docker.com/r/jsavargas/telethon_downloader/)
[![Docker Stars](https://badgen.net/docker/stars/jsavargas/telethon_downloader?icon=docker&label=stars)](https://hub.docker.com/r/jsavargas/telethon_downloader/)
[![Docker Image Size](https://badgen.net/docker/size/jsavargas/telethon_downloader?icon=docker&label=image%20size)](https://hub.docker.com/r/jsavargas/telethon_downloader/)
![Github stars](https://badgen.net/github/stars/jsavargas/telethon_downloader?icon=github&label=stars)
![Github forks](https://badgen.net/github/forks/jsavargas/telethon_downloader?icon=github&label=forks)
![Github last-commit](https://img.shields.io/github/last-commit/jsavargas/telethon_downloader)
![Github license](https://badgen.net/github/license/jsavargas/telethon_downloader)

## Find us at:

[![github](https://img.shields.io/badge/github-jsavargas-5865F2?style=for-the-badge&logo=github&logoColor=white&labelColor=101010)](https://github.com/jsavargas/telethon_downloader)
[![docker](https://img.shields.io/badge/docker-jsavargas-5865F2?style=for-the-badge&logo=docker&logoColor=white&labelColor=101010)](https://hub.docker.com/r/jsavargas/telethon_downloader)
[![discord](https://img.shields.io/badge/discord-jsavargas-5865F2?style=for-the-badge&logo=discord&logoColor=white&labelColor=101010)](https://discord.gg/FdJMau8sf6)

<p align="center">
    <img src="https://github.com/jsavargas/telethon_downloader/blob/master/templates/UNRAID/telegram_logo.png?raw=true" alt="alt text" width="25%">
</p>

# [jsavargas/telethon_downloader](https://github.com/jsavargas/telethon_downloader)

# Telegram Bot with Automatic Download

This Telegram Bot, based on the [Telethon](https://github.com/LonamiWebs/Telethon) client, is designed to automatically download multimedia files sent to it. Additionally, it can download videos or audios from YouTube and direct links to files via their URL, intelligently handling `.torrent` files by passing them to the configured torrent client.

# Features

- **Automatic Downloads**: Automatically downloads files sent to the bot, including media sent together as an album/group.
- **Pending Downloads Resume**: On startup, the bot can prompt to resume any downloads that were interrupted or were pending from a previous session.
- **Cancel In-Progress Downloads**: An inline "Cancel Download" button is shown while a file is downloading.
- **YouTube & Direct Links**: Download videos/audios from YouTube — including playlists, with the option to grab just the first video or the whole list, and to fetch Video, Audio, or Both — plus files from direct URLs.
- **Torrent Support**: Handles `.torrent` files and magnet links via a configured torrent client (qBittorrent API, with category selection, or a watch folder).
- **File Organization**:
    - Sorts files into folders based on file extension, group/channel ID, or keywords/regex in the filename.
    - Default sorting: completed files are moved to a `completed` subfolder and temporary downloads to an `incompleted` subfolder within the base path.
    - Customizable paths via `config.ini` or bot commands.
- **Conflict Resolution**: Compares MD5 hashes of existing files to avoid duplicates, adding numeric suffixes when content differs.
- **Interactive Commands**:
    - `/rename`: Rename downloaded files.
    - `/addpath`: Interactive menu to configure download paths for extensions and groups.
    - `/addextensionpath` & `/addgrouppath`: Quickly set download paths with a single command.
    - `/id`: Shows your user ID or the ID of the replied message's origin.
- **Directory Browser**: An interactive directory browser to pick a destination folder — shown after each download completes (with "Move"/"Ok" options) and when configuring paths via `/addpath`. Includes "Up" and "New Folder" functionality, and can move an entire group of files at once.

Enjoy an automated and organized downloading experience with telethon_downloader!

![](images/e8de6c34276cd714552a94f378e77948.gif)

![](images/download-youtube.png)

# Running Telethon Downloader

## Environment Variables:

Pull or build the docker image and launch it with the following environment variables:

- **TG_AUTHORIZED_USER_ID** (or **AUTHORIZED_USER_ID**): Telegram chat ID authorized to use the bot. Supports a comma-separated list of IDs (e.g., `123456,789012`).
- **TG_API_ID** (or **API_ID**): Telegram API key generated at [my.telegram.org](https://my.telegram.org/).
- **TG_API_HASH** (or **API_HASH**): Telegram API hash.
- **TG_BOT_TOKEN** (or **BOT_TOKEN**): Telegram BOT token generated via [@BotFather](https://telegram.me/botfather).
- **DOWNLOAD_PATH** (or **TG_DOWNLOAD_PATH**) [OPTIONAL]: Base path for completed downloads (default: `/download`). Files will be sorted into `completed` and `incompleted` subfolders.
- **DOWNLOAD_PATH_TORRENTS** [OPTIONAL]: Folder for `.torrent` files in `watch` mode (default: `/watch`).
- **PATH_CONFIG** [OPTIONAL]: Path where configuration files and history are stored (default: `/config/`).
- **TORRENT_MODE** [OPTIONAL]: Mode for torrent handling. Set to `qbittorrent` for API integration, or `watch` for watch folder (default: `watch`).
- **QBT_HOST** [REQUIRED if TORRENT_MODE is 'qbittorrent']: Hostname or IP of the qBittorrent Web UI.
- **QBT_PORT** [OPTIONAL]: Port of the qBittorrent Web UI (default: `8080`).
- **QBT_USERNAME** [OPTIONAL]: Username for qBittorrent authentication.
- **QBT_PASSWORD** [OPTIONAL]: Password for qBittorrent authentication.
- **PUID** [OPTIONAL]: User ID for file ownership.
- **PGID** [OPTIONAL]: Group ID for file ownership.
- **TZ** [OPTIONAL]: System timezone (e.g., `America/Santiago`).
- **TG_MAX_PARALLEL** (or **MAX_CONCURRENT_TASKS**) [OPTIONAL]: Maximum parallel downloads (default: `4`).
- **TG_PROGRESS_DOWNLOAD** (or **PROGRESS_DOWNLOAD**) [OPTIONAL]: Show download progress (default: `True`).
- **PROGRESS_STATUS_SHOW** [OPTIONAL]: Progress update frequency in percentage (default: `10`).
- **YOUTUBE_FORMAT_VIDEO** [OPTIONAL]: YouTube video format (default: `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best`).
- **YOUTUBE_FORMAT_AUDIO** [OPTIONAL]: YouTube audio format (default: `bestaudio/best`).
- **YOUTUBE_DEFAULT_DOWNLOAD** [OPTIONAL]: Default choice for YouTube downloads: `video` or `audio` (default: `video`).
- **YOUTUBE_TIMEOUT_OPTION** [OPTIONAL]: Seconds to wait for format selection before using default (default: `5`).
- **YOUTUBE_VIDEO_FOLDER** [OPTIONAL]: Path for YouTube videos (default: `/download/youtube/videos`).
- **YOUTUBE_AUDIO_FOLDER** [OPTIONAL]: Path for YouTube audios (default: `/download/youtube/audios`).

## Volumes:

- **/config**: Configuration files, `config.ini`, pending downloads, and history.
- **/download**: Main download folder.
- **/watch**: Watch folder for torrent files (if `TORRENT_MODE=watch`).

# Config File: config.ini

The `config.ini` file organizes downloads into specific paths based on rules.

**Precedence Order:**
1. `KEYWORDS`
2. `REGEX_PATH`
3. `GROUP_PATH`
4. `EXTENSIONS`

### [EXTENSIONS]
```ini
[EXTENSIONS]
mp4 = /download/videos
pdf = /download/documents
```

### [GROUP_PATH]
```ini
[GROUP_PATH]
-100118xxxxxxxx = /download/channel_content
```

### [KEYWORDS]
```ini
[KEYWORDS]
tutorial = /download/tutorials
```

### [REGEX_PATH]
Support for case-insensitive matching with `/pattern/i`.
```ini
[REGEX_PATH]
/Halo/i = /download/Series/Halo
```

### [REMOVE_PATTERNS]
Define patterns to remove from filenames per group or globally (`*`).
```ini
[REMOVE_PATTERNS]
* = _compressed, [720p]
-100123456 = channel_tag
```

# Available Commands

- `/id`: Shows your user ID or the ID of the replied message's origin.
- `/version`: Shows the bot version and internal dependencies.
- `/start`: Shows welcome message and help.
- `/help`: Shows available commands.
- `/rename`: Rename a file by replying to it: `/rename <new_name>`.
- `/addpath`: Interactive menu to add download paths.
- `/addextensionpath`: Usage: `/addextensionpath <ext> <path>` or reply to a file.
- `/addgrouppath`: Usage: `/addgrouppath <id> <path>` or reply to a message.

# Generating Telegram API keys

1. Visit [my.telegram.org](https://my.telegram.org/).
2. Login and go to "API Development tools".
3. Create a new application to get your **API ID** and **API Hash**.

# Creating a Telegram Bot

1. Message [@BotFather](https://telegram.me/botfather) on Telegram.
2. Use `/newbot` and follow the instructions to get your **Bot Token**.

# Docker Compose Example

```yaml
version: '3'
services:
  telethon_downloader:
    image: jsavargas/telethon_downloader
    container_name: telethon_downloader
    restart: unless-stopped
    network_mode: host
    environment:
      - PUID=1000
      - PGID=1000
      - TG_API_ID=your_api_id
      - TG_API_HASH=your_api_hash
      - TG_BOT_TOKEN=your_bot_token
      - TG_AUTHORIZED_USER_ID=your_user_id
      - TORRENT_MODE=qbittorrent
      - QBT_HOST=192.168.1.10
      - TZ=America/Santiago
    volumes:
      - /path/to/config:/config
      - /path/to/download:/download
      - /path/to/watch:/watch
```

# Changelog

## [Version 4.0.15] - 2026-06-05
- **Documentation:** Updated README with missing environment variables and features.
- **Documentation:** Clarified authorized user ID supports comma-separated lists.
- **Documentation:** Added details about default `completed` and `incompleted` subdirectories.
- **Documentation:** Explicitly mentioned the Pending Downloads Resume feature.

## [Version 4.0.14] - 2026-03-15
- **Maintenance:** Updated internal dependencies and improved bot stability.
- **Maintenance:** General bug fixes.

## [Version 4.0.13] - 2025-12-05
- **Feature:** Implemented robust file conflict resolution using MD5 hashes.
- **Enhancement:** Improved download summary accuracy.
