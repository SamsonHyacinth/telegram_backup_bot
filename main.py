import asyncio
import logging
import os

from dotenv import load_dotenv
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message, Chat


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR)

load_dotenv(dotenv_path = ".token/token.txt")

api_hash = os.getenv("API_HASH")
api_id = os.getenv("API_ID")
bot_token = os.getenv("BOT_TOKEN")
backup_channel = os.getenv("BACKUP_CHANNEL")
origin_channel = os.getenv("ORIGIN_CHANNEL")

app = Client(name="zone_file_remover", api_id=api_id, api_hash=api_hash)


@app.on_message(filters.channel & filters.command("backup"))
async def backup(client: Client, message: Message):
    
    messages = []
    msg = client.get_chat_history(chat_id=origin_channel)
    async for m in msg:
        messages.append(m)

    total = 0

    messages = reversed(messages)

    for message in messages:
        await client.copy_message(chat_id=backup_channel, from_chat_id=origin_channel, message_id=message.id)
        total += 1
        await asyncio.sleep(.5)
    

    print(f"Total messages backup : {total}")


print("[Started] Zone file remover bot - waiting for tasks :)")
app.run()