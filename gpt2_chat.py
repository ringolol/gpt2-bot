import random

from chat_logger import get_logger
from gpt2_model import GPTGenerate # gpt-2
from db_models import ChatModel # database


# contexts
INIT_CONTEXT_MULTY = '''Это был отличный солнечный день, мы встретились с моими лучшими друзьями.
- Привет! - сказала я.
- Привет! - ответили они хором.
'''
INIT_CONTEXT_SOLO = '''Это был отличный солнечный день, мы встретились с моим очень хорошим другом.
- Привет. - сказал он.
- Привет. - ответила я.
'''

# gpt-2 parameters
msg_len = 50
top_k = 10
top_p = 0.95
temperature = 1.0

logger = get_logger()


def handle_message(message, user_name, channel, solo=True, p=1.0, always_answer=False):
    
    # get history from sqlite3 database
    try:
        chat_obj = ChatModel.get(ChatModel.name == channel)
    except ChatModel.DoesNotExist:
        chat_obj = ChatModel.create(
            name=channel, 
            history=INIT_CONTEXT_SOLO if solo else INIT_CONTEXT_MULTY
        )

    logger.info(f'''message:
    channel: {channel}
    user: {user_name}
    message: {message}''')

    # delete old history
    if len(chat_obj.history) > 30000:
        chat_obj.history = chat_obj.history[-10000:]
        chat_obj.save()
        logger.info('History shortened')

    # add new message to history
    chat_obj.history += f'- {message} - сказал {"он" if solo else user_name}.\n-'

    # answer only on a fraction of messages
    #   e.g. if random.random() > 0.2, then bot answers only on
    #   20% of messages.

    if not solo and not always_answer and random.random() > p:
        logger.info("unlucky, don't answer.")
        chat_obj.save()
        return

    # generate answer
    raw_output = GPTGenerate(
        chat_obj.history,
        msg_len=msg_len,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature
    )
    raw_answer = raw_output[len(chat_obj.history):].split('\n')[0]
    answer = ''.join([
        sec for inx, sec in enumerate(raw_answer.split(' - ')) if not inx % 2
    ]).strip()

    # upd history
    chat_obj.history += f'{answer}\n'
    chat_obj.save()

    logger.info(f'    answer: {answer}\n' + '='*30)

    # return answer
    return answer