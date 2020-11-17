import logging

import torch
from transformers import AutoTokenizer, AutoModel, AutoModelWithLMHead


logger = logging.getLogger('gpt3_chat_bot')

def init_gpt2():
    global gpt2_tokenizer, gpt2_model, CONTEXT_LEN

    logger.info('Initializing GPT-2 model')
    model_name = "sberbank-ai/rugpt3large_based_on_gpt2" # "sberbank-ai/rugpt2large"
    CONTEXT_LEN = 2048
    gpt2_tokenizer = AutoTokenizer.from_pretrained(model_name)
    gpt2_model = AutoModelWithLMHead.from_pretrained(model_name).to("cuda")
    logger.info('GPT-2 model is initialized')

def GPTGenerate(context, msg_len=500, top_k=10, top_p=0.95, temperature=1.0):
    encoded_prompt = gpt2_tokenizer.encode(
        context,
        add_special_tokens=False, 
        return_tensors="pt"
    ).to("cuda")

    if len(encoded_prompt[0]) + msg_len > CONTEXT_LEN:
        overflow = len(encoded_prompt[0]) + msg_len - CONTEXT_LEN
        encoded_prompt = encoded_prompt[0][overflow:].view(1, -1)

        logger.info(f'Context shortened during GPTGenerate, new length is {len(encoded_prompt[0])}')

        context = gpt2_tokenizer.decode(
            encoded_prompt[0],
            clean_up_tokenization_spaces=True
        )

    output_sequences = gpt2_model.generate(
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

    output_sequences_dec = gpt2_tokenizer.decode(
        output_sequences,
        clean_up_tokenization_spaces=True
    )

    return output_sequences_dec