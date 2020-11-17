import os
import logging

# telegram
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# gpt-3 chat
from gpt2_chat import handle_message, INIT_CONTEXT_SOLO, INIT_CONTEXT_MULTY
from gpt2_model import GPTGenerate, init_gpt2

from db_models import GenModel, ChatModel


# setup logger
logger = logging.getLogger('gpt3_chat_bot')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('bot.log', 'a', 'utf-8')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger.addHandler(fh)
logger.addHandler(ch)


logger.info('Started')

# init gpt-2 model
init_gpt2()

# env
logger.info('Loading enviroment')
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# telegram init
logger.info('Initializing telegram')
tg_updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
tg_dispatcher = tg_updater.dispatcher
start_message = \
'''Нода — это простенький чат бот основанный на моделе ruGPT-3 от Сбербанка.

Специальные комманды:
/clear — очистить накопленную историю сообщений, на основе которой бот генерирует сообщения (помогает при затупах бота);
/history — посмотреть историю сообщений с точки зрения бота;
/generate НЕКАЯ_СТРОКА — сгенерировать продолжение строки, позволяет напрямую взаимодействовать с моделью минуя интерфейс чата;
(in dev) /settings — поменять настройки модели и чат бота;
(in dev) /persona ... — выбрать личность бота за счет смены начального контекста.'''

# telegram handlers
def tg_start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)

def tg_message(update, context):
    # don't answer bots
    if update.message.from_user.is_bot:
        return
    
    ans = handle_message(
        message=update.message.text, 
        user_name=str(update.message.from_user.first_name), 
        channel=update.effective_chat.id,
        solo=update.message.chat.type == 'private'
    )

    if ans:
        context.bot.send_message(chat_id=update.effective_chat.id, text=ans)

def tg_generate_command(update, context):
    ctx = update.message.text[len('/generate '):]
    gen = GPTGenerate(ctx)[len(ctx):]
    username = update.message.from_user.username
    context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f'<i>{ctx}</i>{gen}',
        parse_mode='HTML'
    )
    logger.info(f'generation:\n    username: {username}\n    ctx: {ctx}\n    gen: {gen}\n' + '='*30)
    GenModel.create(username=username, context=ctx, generation=gen)

def tg_history_command(update, context):
    logger.info('Showing history')
    try:
        chat_obj = ChatModel.get(ChatModel.name == update.effective_chat.id)
        hist = chat_obj.history
    except ChatModel.DoesNotExist:
        hist = ''

    context.bot.send_message(chat_id=update.effective_chat.id, text=f'History: \n{hist}')

def tg_clear_command(update, context):
    logger.info('Clearing history')
    try:
        chat_obj = ChatModel.get(ChatModel.name == update.effective_chat.id)
        solo = update.message.chat.type == 'private'
        chat_obj.history = INIT_CONTEXT_SOLO if solo else INIT_CONTEXT_MULTY
        chat_obj.save()
    except ChatModel.DoesNotExist:
        pass

    context.bot.send_message(chat_id=update.effective_chat.id, text='cleared!')

    
# attach tg handlers
# /start
tg_start_handler = CommandHandler('start', tg_start)
tg_dispatcher.add_handler(tg_start_handler)

# common messages
tg_message_handler = MessageHandler(Filters.text & (~Filters.command), tg_message)
tg_dispatcher.add_handler(tg_message_handler)

# /generate [строка]
tg_generate_handler = CommandHandler('generate', tg_generate_command)
tg_dispatcher.add_handler(tg_generate_handler)

# /history
tg_history_handler = CommandHandler('history', tg_history_command)
tg_dispatcher.add_handler(tg_history_handler)

# /clear
tg_clear_handler = CommandHandler('clear', tg_clear_command)
tg_dispatcher.add_handler(tg_clear_handler)

tg_updater.start_polling()
logger.info('Telegram started')