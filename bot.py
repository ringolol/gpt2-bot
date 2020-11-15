import os
import random

# discord + telegram
import discord
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# websocket libraries
import asyncio
import websockets

# nlp libraries
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelWithLMHead


print('starting bot...')
# init nlp model
CONTEXT_LEN = 2048
INIT_CONTEXT_MULTY = '''Это был отличный солнечный день, мы встретились с моими лучшими друзьями.
- Привет! - сказала я.
- Привет! - ответили они хором.
'''
INIT_CONTEXT_SOLO = '''Это был отличный солнечный день, мы встретились с моим очень хорошим другом.
- Привет. - сказал он.
- Привет. - ответила я.
'''
model_name = "sberbank-ai/rugpt3large_based_on_gpt2" # "sberbank-ai/rugpt2large"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelWithLMHead.from_pretrained(model_name)
model.to("cuda")
print('gpt-3 initialized.')

# gpt-3 parameters
msg_len = 50
top_k = 10
top_p = 0.95
temperature = 1.0
history = {}

# env
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# telegram init
tg_updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
tg_dispatcher = tg_updater.dispatcher

# discord init
discord_bot = discord.Client()


def GPT3_answer(context, msg_len=50, top_k=10, top_p=0.95, temperature=1.0):
    '''GPT-3 for generating an answer to a message'''

    encoded_prompt = tokenizer.encode(
        context,
        add_special_tokens=False, 
        return_tensors="pt"
    ).to("cuda")

    if len(encoded_prompt[0]) + msg_len > CONTEXT_LEN:
        overflow = len(encoded_prompt[0]) + msg_len - CONTEXT_LEN
        print(encoded_prompt.shape)
        encoded_prompt = encoded_prompt[0][overflow:].view(1, -1)
        print(encoded_prompt.shape)

        print(f'Context shortened, new len: {len(encoded_prompt[0])}')

        context = tokenizer.decode(
            encoded_prompt[0],
            clean_up_tokenization_spaces=True
        )

    output_sequences = model.generate(
        input_ids=encoded_prompt,
        max_length=len(encoded_prompt[0])+msg_len,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        repetition_penalty=1.,
        do_sample=True,
        num_return_sequences=1,
        pad_token_id=50256,
    )[0].tolist()

    output_sequences_dec = tokenizer.decode(
        output_sequences,
        clean_up_tokenization_spaces=True
    )
    answer = output_sequences_dec[len(context):].split('\n')[0]

    stripped_answer = ''.join([
        sec for inx, sec in enumerate(answer.split(' - ')) if not inx % 2
    ]).strip()

    return stripped_answer


def handle_message(message, user_name, channel, solo=True, p=1.0):
    global history

    print('='*15)
    print('message:')
    print(f'\tchannel: {channel}\n\tuser: {user_name}\n\tmessage: {message}')
    print('='*15)

    if channel not in history:
        history[channel] = INIT_CONTEXT_SOLO if solo else INIT_CONTEXT_MULTY

    # special commands
    if message == 'clear':
        history[channel] = INIT_CONTEXT_SOLO if solo else INIT_CONTEXT_MULTY
        return 'cleared!'
    elif message == 'history':
        return f'History: \n{history[channel]}'

    # delete old history
    if len(history[channel]) > 30000:
        history[channel] = history[channel][-10000:]
        print(f'History shortened.')

    # add new message to history
    history[channel] += f'- {message} - сказал {user_name}.\n-'

    # answer only on a fraction of messages
    #   e.g. if random.random() > 0.2, then bot answers only on
    #   20% of messages.
    if random.random() > p:
        return

    # generate answer
    ans = GPT3_answer(
        history[channel],
        msg_len=msg_len,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature
    )

    # upd history
    history[channel] += f'{ans}\n'

    print(f'\tanswer: {ans}')
    print('='*15)

    # return answer
    return ans


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
        solo=False #?
    )
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=ans)
    
# attach tg handlers
tg_start_handler = CommandHandler('start', tg_start)
tg_dispatcher.add_handler(tg_start_handler)

tg_message_handler = MessageHandler(Filters.text & (~Filters.command), tg_message)
tg_dispatcher.add_handler(tg_message_handler)


# discord handlers
@discord_bot.event
async def on_ready():
    print(f'{discord_bot.user} has connected to Discord!')

@discord_bot.event
async def on_message(message):
    # don't answer bots
    if message.author.bot:
        return

    ans = handle_message(
        message=message.content, 
        user_name=str(message.author).split("#")[0], 
        channel=f'ds-{message.channel.id}',
        solo=False
    )

    await message.channel.send(ans)
    

# websocket handler
async def ws_chat_handler(websocket, path):
    '''chat for websocket'''
    while True:
        message = await websocket.recv()
        ans = handle_message(
            message=message, 
            user_name='он', 
            channel=f'ws-{websocket.remote_address[0]}'
        )
        await websocket.send(ans)


# start telegram and discord bots
tg_updater.start_polling()
# discord_bot.run(DISCORD_TOKEN)
ws_chat_server = websockets.serve(ws_chat_handler, "192.168.1.3", 8765)

# start discord and websocket
try:
    asyncio.get_event_loop().run_until_complete(ws_chat_server)
    print('bot ready.')
    asyncio.get_event_loop().run_until_complete(discord_bot.start(DISCORD_TOKEN))
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    asyncio.get_event_loop().run_until_complete(discord_bot.logout())
    # cancel all tasks lingering
finally:
    asyncio.get_event_loop().close()