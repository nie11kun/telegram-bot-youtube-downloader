# telegram-bot-youtube-downloader

Before use:
  - add system env: **BOT_TOKEN**, **INS_ACCOUNT**

Usage:
  - `/dl` then send the media url
  - The bot will download the video and send it
      - If the video is larger than 50MB, it is split into smaller parts

This script require:
  - Python3.5 and above
  - Telegram python api https://github.com/python-telegram-bot/python-telegram-bot
  - yt-dlp https://github.com/yt-dlp/yt-dlp
  - instaloader https://instaloader.github.io/index.html
