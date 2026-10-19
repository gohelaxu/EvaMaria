import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from motor.motor_asyncio import AsyncIOMotorClient

# Render Keep-Alive Port Server
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_health():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

threading.Thread(target=start_health, daemon=True).start()

API_ID = int(os.environ.get("API_ID", "31875394"))
API_HASH = os.environ.get("API_HASH", "aeec492d2057af0d11b8aa13419c918d")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URI = os.environ.get("DATABASE_URI")
STORAGE_CHANNEL = int(os.environ.get("CHANNELS", "-1003711355659"))

mongo = AsyncIOMotorClient(DATABASE_URI)
db = mongo["Cluster0"]
files_col = db["telegram_files"]

app = Client("evamaria_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if len(message.command) > 1:
        # Deep-link delivery
        file_id_str = message.command[1]
        doc = await files_col.find_one({"_id": file_id_str})
        if doc:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=STORAGE_CHANNEL,
                message_id=doc["msg_id"]
            )
            return
        else:
            await message.reply_text("❌ File expired athva database ma nathi.")
            return

    await message.reply_text(
        "🎬 **Welcome to Movie Search Bot!**\n\n"
        "Tame je movie joiye tenu name ahiya lakho.\n"
        "Ex: `Chhello Divas` athva `Chal Jivi Laiye`"
    )

@app.on_message(filters.chat(STORAGE_CHANNEL) & (filters.video | filters.document))
async def auto_save_channel(client, message):
    file_obj = message.video or message.document
    file_name = file_obj.file_name or message.caption or "Unknown Movie"
    size_mb = round(file_obj.file_size / (1024 * 1024), 2)
    doc_id = f"{message.id}_{file_obj.file_unique_id}"
    await files_col.update_one(
        {"_id": doc_id},
        {"$set": {"name": file_name, "msg_id": message.id, "size": size_mb}},
        upsert=True
    )
    print(f"[*] Indexed: {file_name} ({size_mb} MB)")

@app.on_message(filters.command("index") & filters.private)
async def manual_index(client, message):
    status = await message.reply_text("⏳ Storage channel scan thai rahi chhe...")
    count = 0
    async for msg in client.get_chat_history(STORAGE_CHANNEL):
        if msg.video or msg.document:
            file_obj = msg.video or msg.document
            file_name = file_obj.file_name or msg.caption or "Unknown Movie"
            size_mb = round(file_obj.file_size / (1024 * 1024), 2)
            doc_id = f"{msg.id}_{file_obj.file_unique_id}"
            await files_col.update_one(
                {"_id": doc_id},
                {"$set": {"name": file_name, "msg_id": msg.id, "size": size_mb}},
                upsert=True
            )
            count += 1
    await status.edit_text(f"✅ Indexed {count} files successfully!")

@app.on_message(filters.text & filters.private & ~filters.command)
async def search_handler(client, message):
    query = message.text.strip()
    regex = {"$regex": query, "$options": "i"}
    cursor = files_col.find({"name": regex}).limit(10)
    results = await cursor.to_list(length=10)

    if not results:
        await message.reply_text(f"❌ `{query}` mate koi file mali nathi.")
        return

    keyboard = []
    for r in results:
        btn_text = f"📁 {r['name']} ({r['size']} MB)"
        # Deep link direct file delivery
        me = await client.get_me()
        deep_link = f"https://t.me/{me.username}?start={r['_id']}"
        keyboard.append([InlineKeyboardButton(btn_text, url=deep_link)])

    await message.reply_text(
        f"🎬 **Found files for:** `{query}`\nNiche na button par click kari direct download karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

print("[*] Starting Fast Movie Engine Bot...")
app.run()
