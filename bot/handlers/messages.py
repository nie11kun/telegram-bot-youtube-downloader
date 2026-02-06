import logging
# from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.services import downloader
from bot.handlers.utils import format_keyboard

logger = logging.getLogger(__name__)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    status_msg = await update.message.reply_text("Fetching info...")
    
    try:
        formats = await downloader.get_formats(url)
        if not formats:
            await status_msg.edit_text("No suitable formats found.")
            return

        # Generate Keyboard
        keyboard = format_keyboard(formats)
        
        # Store URL in chat_data keyed by the bot's message_id
        if context.chat_data is None:
             context.chat_data = {}
             
        context.chat_data[f"msg_{status_msg.message_id}"] = url
        
        await status_msg.edit_text("Select format:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"Error handling link {url}: {e}")
        await status_msg.edit_text("Failed to fetch info. Is the link valid?")
