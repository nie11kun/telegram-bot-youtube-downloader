import logging

from telegram import InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters, CommandHandler

from vid_utils import Video, BadLink

updater = Updater(token='YOUR TOKEN', use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_format(update, context):
    query = update.callback_query
    logger.info("from {}: {}".format(update.message.chat_id, update.message.text)) # "history"

    if 'instagram.com' in update.message.text:
        video = Video(update.message.text)
        try:
            video.insDownload()

            with video.send_ins() as files:
                for f in files:
                    try:
                        context.bot.send_document(chat_id=update.effective_chat.id, document=open(f, 'rb'), timeout=600)#open with binary file and send data
                    except TimeoutError :
                        context.bot.send_message(chat_id=update.effective_chat.id, text="Tansfer timeout, place try again later")
                        video.removeIns()
                context.bot.send_message(chat_id=update.effective_chat.id, text="Finished")
                video.removeIns()
        except BadLink:
            update.message.reply_text("Bad link")
        return
    try:
        video = Video(update.message.text, init_keyboard=True)
    except BadLink:
        update.message.reply_text("Bad link")
    else:
        reply_markup = InlineKeyboardMarkup(video.keyboard)
        update.message.reply_text('Choose format:', reply_markup=reply_markup)


def download_choosen_format(update, context):
    query = update.callback_query
    resolution_code, link, send_type = query.data.split(' ', 2)#setting the max parameter to 1, will return a list with 2 elements!

    context.bot.edit_message_text(text="Downloading...",
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

    video = Video(link)
    video.download(resolution_code)

    if send_type == 'file':
        with video.send_file() as files:
            for f in files:
                try:
                    context.bot.send_document(chat_id=query.message.chat_id, document=open(f, 'rb'), timeout=600)#open with binary file and send data
                except TimeoutError :
                    context.bot.send_message(chat_id=update.effective_chat.id, text="Tansfer timeout, place try again later")
                    video.remove()
            context.bot.send_message(chat_id=update.effective_chat.id, text="Finished")
            video.remove()
    else:
        file_link = video.send_link()
        context.bot.send_message(chat_id=update.effective_chat.id, text=file_link)

def help_cmd(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=
       "This is Marco's personal Bot.\n\n"
       "It can do some amazing jobs!")

def dl_cmd(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="send me the media url")
    dispatcher.add_handler(MessageHandler(Filters.text, get_format))
    dispatcher.add_handler(CallbackQueryHandler(download_choosen_format))# call back query

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def error(update, context, error):
    context.bot.send_message(chat_id=update.effective_chat.id, text=('"%s" caused error "%s"', context, error))
    logger.warning('"%s" caused error "%s"', context, error)

dispatcher.add_handler(CommandHandler("help", help_cmd))
dispatcher.add_handler(CommandHandler("dl", dl_cmd))
dispatcher.add_handler(MessageHandler(Filters.text, echo))
dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()
