import asyncio
import websockets
import os
from aiohttp import web
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = -1002484572207
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://your-app.onrender.com

bot = AsyncTeleBot(BOT_TOKEN)
connected_clients = set()

# -------------------- WebSocket --------------------

async def ws_handler(websocket):
    print("[Server] New client connected.")
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print("[Server] Client disconnected.")

# -------------------- Telegram Handler --------------------

@bot.channel_post_handler(func=lambda message: message.chat.id == CHANNEL_ID)
async def handle_channel_post(message):
    if message.text:
        print(f"[Telegram] New signal received:\n{message.text}")

        if connected_clients:
            await asyncio.gather(
                *(ws.send(message.text) for ws in connected_clients),
                return_exceptions=True
            )

# -------------------- Webhook Receiver --------------------

async def handle_webhook(request):
    if request.method == "POST":
        json_data = await request.json()
        update = Update.de_json(json_data)
        await bot.process_new_updates([update])
        return web.Response()
    return web.Response(status=403)

# -------------------- Main --------------------

async def main():
    port = int(os.environ.get("PORT", 10000))
    host = "0.0.0.0"

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=WEBHOOK_URL)

    app = web.Application()
    app.router.add_post("/", handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    print("Webhook set successfully.")
    print(f"Server running on port {port}")

    async with websockets.serve(ws_handler, host, 8765):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())