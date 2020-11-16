from peewee import *


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


db.create_tables([ChatModel], safe=True)