from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel, SearchField, RowIDField

from chat_logger import get_logger


logger = get_logger()

logger.info('Inializing database')
db = SqliteExtDatabase('bot.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
}) # SqliteDatabase


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

class SpecialUsers(BaseModel):
    user = CharField(primary_key=True)
    flag = CharField()

class QA(BaseModel, FTSModel):
    rowid = RowIDField()
    question = SearchField()
    answer = SearchField(unindexed=True)


# create tables if they don't exist
db.create_tables([ChatModel, GenModel, SpecialUsers, QA], safe=True)
logger.info('Database is initialized')

# add admin
(SpecialUsers.insert(user='ringolol', flag='admin')
    .on_conflict_ignore()
    .execute())