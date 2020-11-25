from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel, SearchField, RowIDField

from chat_logger import get_logger


logger = get_logger()

logger.info('Inializing database')

# create db instance, as alternative use SqliteDatabase (no fts)
db = SqliteExtDatabase('bot.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})


class BaseModel(Model):
    class Meta:
        database = db # db to use

class ChatModel(BaseModel):
    '''chat history'''
    name = CharField(unique=True)
    history = CharField()

class GenModel(BaseModel):
    '''generated texts'''
    username = CharField()
    context = CharField()
    generation = CharField()

class SpecialUsers(BaseModel):
    '''admins and banned users'''
    user = CharField(primary_key=True)
    flag = CharField()

class QA(BaseModel, FTSModel):
    '''questions and answers'''
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