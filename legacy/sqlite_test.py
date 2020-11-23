import sqlite3

conn = sqlite3.connect('bot.db', isolation_level=None)

try:
    conn.execute('''
    CREATE TABLE chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unique_name TEXT UNIQUE NOT NULL,
        history TEXT NOT NULL DEFAULT ""
    )''')
except Exception:
    pass

conn.execute('''INSERT INTO chats (unique_name, history)
VALUES (?, ?)''', ('test_name3', 'test_history'))

conn.close()