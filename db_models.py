from peewee import *

from chat_logger import get_logger


logger = get_logger()

logger.info('Inializing database')
db = SqliteDatabase('bot.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})


class BaseModel(Model):
    class Meta:
        # db to use
        database = db 

class ChatModel(BaseModel):
    name = CharField(unique=True)
    history = CharField()

class GenModel(BaseModel):
    username = CharField()
    context = CharField()
    generation = CharField()


# create tables if they don't exist
db.create_tables([ChatModel, GenModel], safe=True)
logger.info('Database is initialized')