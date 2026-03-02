import asyncio
import websockets
import os
from telebot.async_telebot import AsyncTeleBot

BOT_TOKEN = "8290696483:AAG-yonVayadxER2bWAUUVzxV0tOxhTGYws"
CHANNEL_ID = -1002484572207 

bot = AsyncTeleBot(BOT_TOKEN)
connected_clients = set()

async def ws_handler(websocket):
    print("[Server] New client connected.")
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print("[Server] Client disconnected.")

@bot.channel_post_handler(func=lambda message: message.chat.id == CHANNEL_ID)
async def handle_channel_post(message):
    if message.text:
        print(f"[Telegram] New signal received:\n{message.text}")
        
        if connected_clients:
            await asyncio.gather(
                *(ws.send(message.text) for ws in connected_clients),
                return_exceptions=True
            )

async def main():
    port = int(os.environ.get("PORT", 8765))
    host = "0.0.0.0" 
    
    print(f"Starting WebSocket server on port {port}...")
    
    # 🔥 ده اللي بيحل 409
    await bot.delete_webhook()
    
    async with websockets.serve(ws_handler, host, port):
        print("Starting Telegram bot polling...")
        await bot.polling(non_stop=True, skip_pending=True)

if __name__ == '__main__':
    asyncio.run(main())

