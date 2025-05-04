import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Message, Chat

# load configurations
load_dotenv(dotenv_path = ".token/token.env")

API_HASH = os.getenv("API_HASH")
API_ID = os.getenv("API_ID")
bot_token = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("ORIGIN_CHANNEL")

app = Client(name="zone_file_remover", api_id=API_ID, api_hash=API_HASH)


@app.on_message(filters.channel & filters.command(commands=["delete"], prefixes=["!", "/"]))
async def forward(client: Client, message: Message):
    chat: Chat = message.chat
    await client.delete_messages(chat_id=chat.id, message_ids=message.id)
    messages = client.get_chat_history(chat_id=chat.id)
    total = 0
    async for message in messages:
        await client.delete_messages(chat_id=chat.id, message_ids=message.id)
        print(
            f"Message {message.text} has been deleted - {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}")
        total += 1
        await asyncio.sleep(.5)
    print(f"Total messages deleted : {total}")


print("[Started] Zone file remover bot - waiting for tasks :)")
app.run()