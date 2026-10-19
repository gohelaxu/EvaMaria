import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import asyncio
from pyrogram import Client
from info import API_ID, API_HASH, BOT_TOKEN

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="EvaMaria",
            api_id=int(API_ID),
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins")
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        print(f"[{me.first_name}] Bot Started Successfully!")

    async def stop(self, *args):
        await super().stop()
        print("Bot Stopped.")

if __name__ == "__main__":
    Bot().run()
