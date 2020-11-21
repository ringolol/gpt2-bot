import logging

def init_logger():
    '''init logger'''

    logger = logging.getLogger('gpt3_chat_bot')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('bot.log', 'a', 'utf-8')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info('Started')
    return logger

def get_logger():
    '''get "gpt3_chat_bot" logger'''
    return logging.getLogger('gpt3_chat_bot')