import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.config import settings
from bot.handlers import start_cmd, help_cmd, handle_link, download_callback

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not settings.BOT_TOKEN:
        print("Error: BOT_TOKEN not set!")
        return

    application = ApplicationBuilder().token(settings.BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))

    # Callbacks
    application.add_handler(CallbackQueryHandler(download_callback))

    # Messages (Links)
    # Filter for standard HTTP links. 
    # Note: Telegram entity filters are better but regex is simple and effective for now.
    http_filter = filters.Regex(r'^http')
    application.add_handler(MessageHandler(filters.TEXT & http_filter, handle_link))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
