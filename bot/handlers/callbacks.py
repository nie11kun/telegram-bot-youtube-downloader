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
        # Download returns a list of files
        downloaded_files = await downloader.download_video(url, format_id)
        
        all_chunks = []
        
        # Process each downloaded file
        for file_path in downloaded_files:
             # Check size and split if needed
             file_size = os.path.getsize(file_path)
             _, ext = os.path.splitext(file_path)
             is_image = ext.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.heic']
             
             if not is_image and file_size > settings.MAX_FILE_SIZE:
                 try:
                    await query.edit_message_text(f"Processing large file: {os.path.basename(file_path)}...")
                    chunks = await processor.split_file(file_path, settings.MAX_FILE_SIZE)
                    all_chunks.extend([(c, False) for c in chunks]) # False = not image
                 except Exception as e:
                    logger.error(f"Split failed for {file_path}: {e}")
                    # Skip this file or continue?
                    continue
             else:
                 all_chunks.append((file_path, is_image))

        if not all_chunks:
             await query.edit_message_text("No files processable.")
             return

        await query.edit_message_text(f"Uploading {len(all_chunks)} files...")
        
        for chunk_path, is_img in all_chunks:
            try:
                with open(chunk_path, 'rb') as f:
                    if is_img:
                         await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=f,
                            read_timeout=settings.DEFAULT_TIMEOUT,
                            write_timeout=settings.DEFAULT_TIMEOUT,
                            connect_timeout=settings.DEFAULT_TIMEOUT
                        )
                    else:
                        await context.bot.send_document(
                            chat_id=update.effective_chat.id,
                            document=f,
                            read_timeout=settings.DEFAULT_TIMEOUT,
                            write_timeout=settings.DEFAULT_TIMEOUT,
                            connect_timeout=settings.DEFAULT_TIMEOUT
                        )
            except Exception as e:
                 logger.error(f"Failed to send {chunk_path}: {e}")
                
        await query.edit_message_text("Finished.")
        
        # Cleanup
        for f_path in downloaded_files:
             if os.path.exists(f_path):
                 os.remove(f_path)
                 
        for c, _ in all_chunks:
            if os.path.exists(c):
                os.remove(c)
                
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await query.edit_message_text(f"Error: {str(e)}")
