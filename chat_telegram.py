from telegram.ext import Updater, CommandHandler, MessageHandler

from chat_logger import get_logger
from chat_telegram_handlers import handlers


logger = get_logger()


class TelegramBot:
    def start(self):
        '''start telegram polling'''
        logger.info('Starting telegram')
        self.tg_updater.start_polling()
        logger.info('Telegram is started')

    def __init__(self, tg_token):
        logger.info('Initializing telegram')
        self.tg_updater = Updater(token=tg_token, use_context=True)
        self.tg_dispatcher = self.tg_updater.dispatcher

        for tp, fltr, call_back in handlers:
            fun = CommandHandler if tp == 'cmd' else MessageHandler
            hr = fun(fltr, call_back)
            self.tg_dispatcher.add_handler(hr)
