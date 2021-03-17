# telegram-bot-youtube-downloader

Before use:
  - Change TOKEN with your token in main.py
  - Change insAccount with your instagram account name in vid_utils.py

Usage:
  - Send link of video (@vid inline is comfortable)
  - The bot will download the video and send it
      - If the video is larger than 50MB, it is split into smaller parts

This script require:
  - Python3.5
  - Telegram python api https://github.com/python-telegram-bot/python-telegram-bot
  - youtube-dl https://github.com/rg3/youtube-dl/ (installed on the machine)
  - instaloader https://instaloader.github.io/index.html
