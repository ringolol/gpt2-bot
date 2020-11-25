import re

from peewee import IntegrityError
from telegram.ext import Filters

from chat_logger import get_logger
from chat_gpt2 import answer_message, INIT_CONTEXT_SOLO, INIT_CONTEXT_MULTY
from gpt2_model import GPTGenerate
from chat_db_models import GenModel, ChatModel, SpecialUsers, QA
from chat_lemmatizer import RuLemma


logger = get_logger()

lemma = RuLemma()

re_botname = r'\s?@rugpt3_bot\s?'
re_com = r'(?:/{0})(?:@[^\s]+)?\s(.*)'
re_qa = r'(?:/qa)(?:@[^\s]+)?((?:\s\[\[.*?\]\]){2,})'

START_MESSAGE = \
'''Нода — это простенький чат бот основанный на моделе ruGPT-3 от Сбербанка.

Специальные комманды:
/clear — очистить историю сообщений
/history — посмотреть историю сообщений
/generate СТРОКА — сгенерировать продолжение строки
(in dev) /settings — настройки чат бота'''

'''
clear - очистить историю сообщений
history - посмотреть историю сообщений
generate - сгенерировать продолжение строки
ban - добавить username пользователя в черный список
unban - убрать пользователя из черного списка
qa - добавить QA, пример: /qa [[ВОПРОС]] [[ОТВЕТ]]
q - найти ответ на вопрос в QAs
'''


def get_cmd_par(cmd, txt):
    '''returns the parameter (single) of the command'''
    return re.match(
        re_com.format(cmd),
        txt,
        re.DOTALL
    ).group(1)

def tg_start(update, context):
    '''/start'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=START_MESSAGE)

def tg_message(update, context):
    '''handle common messages by answering them'''

    # don't answer bots (including itself)
    if update.message.from_user.is_bot:
        return

    # input message or a question
    qst = update.message.text
    
    # always answer on a private message or a reply
    always_answer = False
    if '@rugpt3_bot' in qst or update.message.reply_to_message is not None:
        always_answer = True
        qst = re.sub(re_botname, ' ', qst)
    
    # try to generate an answer
    ans = answer_message(
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
    '''use gpt-2 to generate continuation of the given text'''
    ctx = get_cmd_par('generate', update.message.text)

    if not ctx:
        context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text='Для генерации используйте: /generate СТРОКА')
        return
    
    logger.info('Generating')
    # generate continuation
    gen = GPTGenerate(ctx)[len(ctx):].rstrip()
    username = update.message.from_user.username
    # return generation
    context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f'<b>{ctx}</b>{gen}',
        parse_mode='HTML'
    )
    logger.info(f'generation:\n    username: {username}\n    ctx: {ctx}\n    gen: {gen}\n' + '='*30)
    # save generation into the db
    GenModel.create(username=username, context=ctx, generation=gen)

def tg_history_command(update, context):
    '''return the history of the conversation between the user/group and the bot'''

    logger.info('Showing history')
    try:
        chat_obj = ChatModel.get(ChatModel.name == update.effective_chat.id)
        hist = chat_obj.history
    except ChatModel.DoesNotExist:
        hist = ''

    context.bot.send_message(chat_id=update.effective_chat.id, text=f'History: \n{hist}')

def tg_clear_command(update, context):
    '''clear chat histrory between the user/group and the bot'''

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
    '''ban user by their username, banned users are ignored by the bot'''

    logger.info('Banning user')

    user_to_ban = get_cmd_par('ban', update.message.text).lower()
    username = update.message.from_user.username.lower()

    admins = [res.user for res in SpecialUsers.select().where(SpecialUsers.flag == 'admin').execute()]

    if username == user_to_ban or username in admins:
        try:
            SpecialUsers.insert(user=user_to_ban, flag='banned').execute()
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'User {user_to_ban} is banned.')
            logger.info(f'User {user_to_ban} is banned')
        except IntegrityError:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Cannot ban {user_to_ban} they are already banned or have a special role.')
            logger.info(f'Cannot ban {user_to_ban}')

def tg_unban_command(update, context):
    '''unban user by their username'''

    logger.info('Unbanning user')

    user_to_unban = get_cmd_par('unban', update.message.text)
    username = update.message.from_user.username.lower()

    admins = [res.user for res in SpecialUsers.select().where(SpecialUsers.flag == 'admin').execute()]
    
    if username == user_to_unban or username in admins:
        try:
            SpecialUsers.get((SpecialUsers.user == user_to_unban) & (SpecialUsers.flag == 'banned')).delete_instance()
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'User {user_to_unban} is unbanned.')
            logger.info(f'User {user_to_unban} is unbanned')
        except SpecialUsers.DoesNotExist:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'User {user_to_unban} is not banned.')
            logger.info(f'User {user_to_unban} is not banned')

def tg_qa_command(update, context):
    '''add a question and an answer pair into the db, preliminarily lemmatizing the question'''

    logger.info('Adding QA')

    match_cmd = re.match(
        re_qa,
        update.message.text,
        re.DOTALL
    )
    username = update.message.from_user.username.lower()
    admins = [res.user for res in SpecialUsers.select().where(SpecialUsers.flag == 'admin').execute()]

    if username in admins:
        try:
            args = match_cmd.group(1).strip()[2:-2].split(']] [[')
            question = args[0]
            answer = args[1]
        except Exception:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Для создания QA используйте: /qa [[ВОПРОС]] [[ОТВЕТ]]')
            logger.info('Cannot add QA, wrong arguments')
            return # bad practice

        lemma_q = lemma.lemma(question)
        QA.insert({
            QA.question: lemma_q,
            QA.answer: answer
        }).execute()
        logger.info(f'QA added:\n\tQ: {question}\n\tQL: {lemma_q}\n\tA: {answer}')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Access denied. Only admins can add QAs.')
        logger.info('Cannot add QA, access denied')
    
def tg_q_command(update, context):
    '''find an answer to the (lemmatized) question in the db'''

    logger.info('Answering to the question (using QA)')

    question = get_cmd_par('q', update.message.text)
    q_lemma = lemma.lemma(question)
    q_query = ' OR '.join(q_lemma.split()) # like in MySQL FTS in the boolean mode
    top_answers = QA.select().where(QA.match(q_query)).order_by(QA.bm25()).limit(10).execute()
    if len(top_answers) > 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=top_answers[0].answer)
        logger.info(f'Answer:\n\tQ: {question}\n\tQL: {q_lemma}\n\tA: {top_answers[0].answer}')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Похожих вопросов нет в базе данных.')
        logger.info(f'Not suitable answer in the db:\n\tQ: {question}\n\tQL: {q_lemma}')


handlers = [
    ('cmd', 'start', tg_start),
    ('cmd', 'generate', tg_generate_command),
    ('cmd', 'history', tg_history_command),
    ('cmd', 'clear', tg_clear_command),
    ('cmd', 'ban', tg_ban_command),
    ('cmd', 'unban', tg_unban_command),
    ('cmd', 'qa', tg_qa_command),
    ('cmd', 'q', tg_q_command),
    ('msg', Filters.text & (~Filters.command), tg_message)
]