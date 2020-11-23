import os

from dotenv import load_dotenv

from chat_logger import init_logger # should be at top
from gpt2_model import init_gpt2
from chat_telegram import TelegramBot


if __name__ == '__main__':
    # setup logger
    logger = init_logger()

    # init gpt-2 model
    init_gpt2()

    # env
    logger.info('Loading enviroment')
    load_dotenv()
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    # init and start telegram
    bot = TelegramBot(TELEGRAM_TOKEN)
    bot.start()
    logger.info('Telegram started')