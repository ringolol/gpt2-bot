# WS server example

# websocket libraries
import asyncio
import websockets

# nlp libraries
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelWithLMHead

# init nlp model
CONTEXT_LEN = 1024
INIT_CONTEXT = '''Это был отличный солнечный день, мы встретились с моим очень хорошим другом.
- Привет. - сказал он.\n- Привет. - ответила я.\n'''
model_name = "sberbank-ai/rugpt2large" # "sberbank-ai/rugpt3large_based_on_gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelWithLMHead.from_pretrained(model_name)
model.to("cuda")


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


async def chat_handler(websocket, path):
    '''chat for websocket'''

    # gpt-3 parameters
    context = INIT_CONTEXT
    msg_len = 50
    top_k = 10
    top_p = 0.95
    temperature = 1.0

    while True:
        # recive message
        try:
            msg = await websocket.recv()
        except Exception:
            print('Disconected!')
            return

        # special commands
        if msg == 'stop':
            await websocket.send('Stopped!')
            asyncio.get_event_loop().stop()
            print(context)
            return
        elif msg == 'clear':
            await websocket.send('Cleared!')
            context = INIT_CONTEXT
            continue
        elif msg == 'history':
            await websocket.send(f'History: \n{context}')
            continue
        elif msg.startswith('context'):
            context = msg[len('context '):] + '\n'
            await websocket.send(f'New context: \n{context}')
            continue
        elif msg.startswith('config'):
            try:
                _, top_k_s, top_p_s, temperature_s = msg.split()
                assert 0 <= float(top_k_s)
                assert 0 <= float(top_p_s) <= 1.0
                assert 0 <= float(temperature_s) <= 1.0
                top_k = top_k_s
                top_p = top_p_s
                temperature = temperature_s
            except Exception:
                await websocket.send('config should be in form:\n\tconfig 10 0.95 1.0')

            await websocket.send(f'config changed:\n\ttop_k={top_k}\n\ttop_p={top_p}\n\ttemperature={temperature}')
            continue
        elif msg.startswith('model'):
            name = msg[len('model '):]
            if name == 'gpt-2':
                model_n = "sberbank-ai/rugpt2large"
            elif name == 'gpt-3':
                model_n = "sberbank-ai/rugpt3large_based_on_gpt2"
            else:
                await websocket.send('No such model, try "gpt-2" or "gpt-3"')
                continue
            await websocket.send(f'Initializing new model: "{model_n}"')
            global tokenizer, model
            del tokenizer
            del model
            tokenizer = AutoTokenizer.from_pretrained(model_n)
            model = AutoModelWithLMHead.from_pretrained(model_n)
            model.to("cuda")
            await websocket.send(f'Model ready.')
            continue


        print(f"They: {msg}")
        context += f'- {msg} - сказал он.\n-'
        
        # generate answer
        ans = GPT3_answer(
            context,
            msg_len=msg_len,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature
        )
        print(f"Me: {ans}")
        context += f'{ans}\n'

        # send answer
        try:
            await websocket.send(ans)
        except Exception:
            print('Disconected!')
            return
        

chat_server = websockets.serve(chat_handler, "192.168.1.3", 8765)
asyncio.get_event_loop().run_until_complete(chat_server)
print('Websocket server started!')
asyncio.get_event_loop().run_forever()