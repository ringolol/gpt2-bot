import logging

def init_logger():
    '''init logger'''

    LOG_FILE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_CMD_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

    logger = logging.getLogger('gpt3_chat_bot')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('bot.log', 'a', 'utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FILE_FORMAT))

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(LOG_CMD_FORMAT))

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info('Started')
    return logger

def get_logger():
    '''get "gpt3_chat_bot" logger'''
    return logging.getLogger('gpt3_chat_bot')