import random

from gpt2_model import GPTGetMessage # gpt-2
from db_models import ChatModel, db # database


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


def handle_message(message, user_name, channel, solo=True, p=1.0):
    
    # get history from sqlite3 database
    try:
        chat_obj = ChatModel.get(ChatModel.name == channel)
    except ChatModel.DoesNotExist:
        chat_obj = ChatModel.create(name=channel, history=INIT_CONTEXT_SOLO)

    print('='*15)
    print('message:')
    print(f'\tchannel: {channel}\n\tuser: {user_name}\n\tmessage: {message}')
    print('='*15)

    # delete old history
    if len(chat_obj.history) > 30000:
        chat_obj.history = chat_obj.history[-10000:]
        chat_obj.save()
        print(f'History shortened.')

    # special commands
    if message == 'clear':
        chat_obj.history = INIT_CONTEXT_SOLO
        chat_obj.save()
        return 'cleared!'
    elif message == 'history':
        return f'History: \n{chat_obj.history}'


    # add new message to history
    chat_obj.history += f'- {message} - сказал {user_name}.\n-'

    # answer only on a fraction of messages
    #   e.g. if random.random() > 0.2, then bot answers only on
    #   20% of messages.
    if random.random() > p:
        chat_obj.save()
        return

    # generate answer
    ans = GPTGetMessage(
        chat_obj.history,
        msg_len=msg_len,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature
    )

    # upd history
    chat_obj.history += f'{ans}\n'
    chat_obj.save()

    print(f'\tanswer: {ans}')
    print('='*15)

    # return answer
    return ans