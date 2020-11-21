import re

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from peewee import IntegrityError

from chat_logger import get_logger
from gpt2_chat import handle_message, INIT_CONTEXT_SOLO, INIT_CONTEXT_MULTY
from gpt2_model import GPTGenerate
from db_models import GenModel, ChatModel, SpecialUsers


logger = get_logger()

START_MESSAGE = \
'''Нода — это простенький чат бот основанный на моделе ruGPT-3 от Сбербанка.

Специальные комманды:
/clear — очистить историю сообщений
/history — посмотреть историю сообщений
/generate СТРОКА — сгенерировать продолжение строки
(in dev) /settings — настройки чат бота'''

re_com = r'(/{0})(@[^\s]+)?\s(.*)'

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

        qst = update.message.text
        always_answer = False

        if '@rugpt3_bot' in qst or update.message.reply_to_message is not None:
            always_answer = True
            qst = re.sub(r'\s?@rugpt3_bot\s?', ' ', qst)
        
        ans = handle_message(
            message=qst, 
            user_name=str(update.message.from_user.first_name), 
            channel=update.effective_chat.id,
            solo=update.message.chat.type == 'private',
            p=0.2,
            always_answer=always_answer
        )

        if ans:
            context.bot.send_message(chat_id=update.effective_chat.id, text=ans)

    def tg_generate_command(update, context):
        match_cmd = re.match(
            re_com.format('generate'),
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

    def tg_ban_command(update, context):
        match_cmd = re.match(
            re_com.format('ban'),
            update.message.text,
            re.DOTALL
        )
        user_to_ban = match_cmd.group(3).lower()
        username = update.message.from_user.username.lower()

        admins = [res.user for res in SpecialUsers.select().where(SpecialUsers.flag == 'admin').execute()]

        if username == user_to_ban or username in admins:
            try:
                SpecialUsers.insert(user=user_to_ban, flag='banned').execute()
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'User {user_to_ban} is banned.')
            except IntegrityError:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'Cannot ban {user_to_ban} they are already banned or have special role.')

    def tg_unban_command(update, context):
        match_cmd = re.match(
            re_com.format('unban'),
            update.message.text,
            re.DOTALL
        )
        user_to_unban = match_cmd.group(3)
        username = update.message.from_user.username.lower()

        admins = [res.user for res in SpecialUsers.select().where(SpecialUsers.flag == 'admin').execute()]
        
        if username == user_to_unban or username in admins:
            try:
                SpecialUsers.get((SpecialUsers.user == user_to_unban) & (SpecialUsers.flag == 'banned')).delete_instance()
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'User {user_to_unban} is unbanned.')
            except SpecialUsers.DoesNotExist:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f'User {user_to_unban} is not banned.')

        

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

    # /ban
    tg_ban_handler = CommandHandler('ban', tg_ban_command)
    tg_dispatcher.add_handler(tg_ban_handler)

    # /unban
    tg_unban_handler = CommandHandler('unban', tg_unban_command)
    tg_dispatcher.add_handler(tg_unban_handler)

    return tg_updater