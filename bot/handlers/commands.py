from telegram import Update
from telegram.ext import ContextTypes

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Send me a link (YouTube, Instagram, etc.) to download."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Supported Sites:\n"
        "- YouTube\n"
        "- Instagram\n"
        "- Twitter (X)\n"
        "- Pornhub\n\n"
        "Just send the link!"
    )
