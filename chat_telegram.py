from chat_logger import get_logger
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from gpt2_chat import handle_message, INIT_CONTEXT_SOLO, INIT_CONTEXT_MULTY
from gpt2_model import GPTGenerate
from db_models import GenModel, ChatModel


logger = get_logger()

START_MESSAGE = \
'''Нода — это простенький чат бот основанный на моделе ruGPT-3 от Сбербанка.

Специальные комманды:
/clear — очистить историю сообщений
/history — посмотреть историю сообщений
/generate СТРОКА — сгенерировать продолжение строки
(in dev) /settings — настройки чат бота'''

def init_telegram(token):
    '''telegram init'''
    logger.info('Initializing telegram')
    tg_updater = Updater(token=token, use_context=True)
    tg_dispatcher = tg_updater.dispatcher

    # telegram handlers
    def tg_start(update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text=START_MESSAGE)

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
        match_cmd = re.match(
            r'(/generate)(@[^\s]+)?\s(.*)',
            update.message.text,
            re.DOTALL
        )
        ctx = match_cmd.group(3)

        if not ctx:
            context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text='Для генерации используйте: /generate СТРОКА')
            return
        
        logger.info('Generating')
        gen = GPTGenerate(ctx)[len(ctx):].rstrip()
        username = update.message.from_user.username
        context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f'<b>{ctx}</b>{gen}',
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

    return tg_updater