# sqlite3
class SQLiteWrapper:
    def __init__(self):
        self.conn = sqlite3.connect('bot.db', isolation_level=None)
        try:
            self.conn.execute('''
            CREATE TABLE chats (
                name TEXT PRIMARY KEY,
                history TEXT NOT NULL DEFAULT ""
            )''')
        except Exception:
            pass

    def get_history(self, key):
        history = self.conn.execute('''
        SELECT history FROM chats WHERE name = ?''', (key,)).fetchone()
        return history

    def close(self):
        self.conn.close()

    def __getitem__(self, key):
        history = self.get_history(key)
        if history is None:
            self.conn.execute('''
            INSERT INTO chats (name, history)
                VALUES (?, ?)''', (key, ""))
            return ""
        return history[0]

    def __setitem__(self, key, value):
        if self.get_history(key) is None:
            query = '''INSERT INTO chats (name, history) VALUES (?, ?)'''
            self.conn.execute(query, (key, value))
        else:
            query = '''UPDATE chats SET history = ? WHERE name = ?'''
            self.conn.execute(query, (value, key))


# discord handlers
@discord_bot.event
async def on_ready():
    print(f'{discord_bot.user} has connected to Discord!')

@discord_bot.event
async def on_message(message):
    # don't answer bots
    if message.author.bot:
        return

    ans = handle_message(
        message=message.content, 
        user_name=str(message.author).split("#")[0], 
        channel=f'ds-{message.channel.id}',
        solo=False
    )

    await message.channel.send(ans)


# websocket handler
async def ws_chat_handler(websocket, path):
    '''chat for websocket'''
    # while True:
    message = await websocket.recv()
    ans = handle_message(
        message=message, 
        user_name='он', 
        channel=f'ws-{websocket.remote_address[0]}'
    )
    await websocket.send(ans)


# start telegram and discord bots
discord_bot.run(DISCORD_TOKEN)
ws_chat_server = websockets.serve(ws_chat_handler, "192.168.1.3", 8765)

# start discord and websocket
try:
    asyncio.get_event_loop().run_until_complete(ws_chat_server)
    print('bot ready.')
    asyncio.get_event_loop().run_until_complete(discord_bot.start(DISCORD_TOKEN))
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    asyncio.get_event_loop().run_until_complete(discord_bot.logout())
    # cancel all tasks lingering
finally:
    asyncio.get_event_loop().close()