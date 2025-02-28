import asyncio
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.types import Message, Chat
from pyrogram.errors import FloodWait


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR)

load_dotenv(dotenv_path = ".token/token.env")

api_hash = os.getenv("API_HASH")
api_id = os.getenv("API_ID")
bot_token = os.getenv("BOT_TOKEN")
backup_channel = os.getenv("BACKUP_CHANNEL")
origin_channel = os.getenv("ORIGIN_CHANNEL")

if not backup_channel or not origin_channel:
    raise ValueError("BACKUP_CHANNEL and ORIGIN_CHANNEL must be set in environment variables")

app = Client(name="backupbot", api_id=api_id, api_hash=api_hash)


@app.on_message(filters.channel & filters.command("backup"))
async def backup(client: Client, message: Message):
    
    messages = []
    msg = client.get_chat_history(chat_id=origin_channel)
    async for m in msg:
        messages.append(m)

    await client.send_message(chat_id=message.chat.id, text=f"Starting backup... {len(messages)} messages to backup")

    messages = reversed(messages)

    total = 0 # Counter to reset the limit of 1500 messages
    for message in messages:
        try:
            await client.copy_message(chat_id=backup_channel, from_chat_id=origin_channel, message_id=message.id)
            total += 1
            await asyncio.sleep(.5)

            # Reset the counter and wait after 1500 messages
            if total == 1500:
                print("1500 messages limit reached, waiting for 16 minutes;"\
                    f"at {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}")
                await asyncio.sleep(960)  # because floodwait time is around 1000 seconds
                total = 0

        except FloodWait as e:
            print(f"FloodWait: Waiting for : {e.value}; " \
                f"at {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
            await asyncio.sleep(float(e.value))

            await client.copy_message(chat_id=backup_channel, from_chat_id=origin_channel, message_id=message.id)
            await asyncio.sleep(.5)


print("[Started] Backup bot - waiting for tasks :)")
app.run()