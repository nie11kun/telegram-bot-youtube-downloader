import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.services import downloader, processor
from bot.config import settings

logger = logging.getLogger(__name__)

async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith("dl:"):
        return
        
    _, format_id, ext = data.split(":", 2)
    
    # Retrieve URL from chat_data
    msg_key = f"msg_{query.message.message_id}"
    url = context.chat_data.get(msg_key)
    
    if not url:
        await query.edit_message_text("Session expired. Please send the link again.")
        return
        
    await query.edit_message_text(f"Downloading {format_id}...")
    
    try:
        # Download
        file_path = await downloader.download_video(url, format_id)
        
        # Check size and split if needed
        await query.edit_message_text("Processing...")
        
        # Limit check
        file_size = os.path.getsize(file_path)
        chunks = [file_path]
        
        if file_size > settings.MAX_FILE_SIZE:
             await query.edit_message_text(f"File too large ({file_size/1024/1024:.1f}MB). Splitting...")
             try:
                chunks = await processor.split_file(file_path, settings.MAX_FILE_SIZE)
             except Exception as e:
                logger.error(f"Split failed: {e}")
                await query.edit_message_text("Failed to split file. It might be too large to send.")
                # Try to send original anyway? No, Telegram will reject.
                return

        await query.edit_message_text("Uploading...")
        
        for chunk in chunks:
            with open(chunk, 'rb') as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    read_timeout=settings.DEFAULT_TIMEOUT,
                    write_timeout=settings.DEFAULT_TIMEOUT,
                    connect_timeout=settings.DEFAULT_TIMEOUT
                )
                
        await query.edit_message_text("Finished.")
        
        # Cleanup
        # remove all chunks and original
        # If chunks == [file_path], we remove it.
        # If split, we remove parts. Original file might still exist if split_file didn't delete it.
        # Our split_file implementation did not delete the original.
        
        if len(chunks) > 1:
             if os.path.exists(file_path):
                 os.remove(file_path)
                 
        for c in chunks:
            if os.path.exists(c):
                os.remove(c)
                
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await query.edit_message_text(f"Error: {str(e)}")
