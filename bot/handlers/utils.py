from telegram import InlineKeyboardButton

def format_keyboard(formats):
    """
    Generate keyboard from formats.
    """
    kb = []
    
    # Simple limit: Top 8 formats
    for f in formats[:8]:
        # Label: "mp4 1080p 50MB"
        # Data: "f_id" (We will infer URL from context)
        
        size_mb = ""
        if f.get('filesize'):
            size_mb = f"{f['filesize'] / 1024 / 1024:.1f}MB"
            
        btn_text = f"{f['ext']} {f['resolution']} {size_mb}"
        callback_data = f"dl:{f['format_id']}:{f['ext']}" # Prefix dl:
        
        kb.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
        
    return kb
