import torch
from transformers import AutoTokenizer, AutoModel, AutoModelWithLMHead


model_name = "sberbank-ai/rugpt3large_based_on_gpt2" # "sberbank-ai/rugpt2large"
CONTEXT_LEN = 2048
gpt2_tokenizer = AutoTokenizer.from_pretrained(model_name)
gpt2_model = AutoModelWithLMHead.from_pretrained(model_name).to("cuda")

def GPTGetMessage(context, msg_len=50, top_k=10, top_p=0.95, temperature=1.0):
    '''GPT-2 generates a message based on context'''

    encoded_prompt = gpt2_tokenizer.encode(
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
    answer = output_sequences_dec[len(context):].split('\n')[0]

    stripped_answer = ''.join([
        sec for inx, sec in enumerate(answer.split(' - ')) if not inx % 2
    ]).strip()

    return stripped_answer