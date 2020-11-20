import os
import re

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from chat_logger import init_logger, get_logger
from gpt2_chat import handle_message, INIT_CONTEXT_SOLO, INIT_CONTEXT_MULTY
from gpt2_model import GPTGenerate, init_gpt2
from chat_telegram import init_telegram


if __name__ == '__main__':
    # setup logger
    init_logger()
    logger = get_logger()

    # init gpt-2 model
    init_gpt2()

    # env
    logger.info('Loading enviroment')
    load_dotenv()
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    # init and start telegram
    tg_updater = init_telegram(TELEGRAM_TOKEN)
    tg_updater.start_polling()
    logger.info('Telegram started')