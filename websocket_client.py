# WS client example

import asyncio
import websockets

async def hello():
    uri = "ws://31.134.153.18:8765"
    # uri = "ws://localhost:8765"
    
    async with websockets.connect(uri, ping_timeout=None, close_timeout=None) as websocket:
        while True:
            try:
                msg = input("You >>> ")
                await websocket.send(msg)
                ans = await websocket.recv()
                print(f"Bot >>> {ans}")
            except Exception:
                print("Connection ended!")
                break
    

asyncio.get_event_loop().run_until_complete(hello())
