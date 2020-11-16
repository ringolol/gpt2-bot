import os

# telegram
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# nlp libraries
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelWithLMHead

from gpt2_chat import handle_message

# env
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# telegram init
tg_updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
tg_dispatcher = tg_updater.dispatcher

# telegram handlers
def tg_start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def tg_message(update, context):
    # don't answer bots
    if update.message.from_user.is_bot:
        return
    
    ans = handle_message(
        message=update.message.text, 
        user_name=str(update.message.from_user.first_name), 
        channel=f'tg-{update.effective_chat.id}',
        solo=False
    )
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=ans)
    
# attach tg handlers
tg_start_handler = CommandHandler('start', tg_start)
tg_dispatcher.add_handler(tg_start_handler)

tg_message_handler = MessageHandler(Filters.text & (~Filters.command), tg_message)
tg_dispatcher.add_handler(tg_message_handler)

tg_updater.start_polling()