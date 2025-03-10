import asyncio
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from telethon import events, TelegramClient as Client
from telethon.tl.types import Message, MessageService
from telethon.errors import FloodWaitError


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING)

load_dotenv(dotenv_path = ".token/token.env")

api_hash = os.getenv("API_HASH")
api_id = os.getenv("API_ID")
bot_token = os.getenv("BOT_TOKEN")
backup_channel = os.getenv("BACKUP_CHANNEL")
origin_channel = os.getenv("ORIGIN_CHANNEL")

if not backup_channel or not origin_channel:
    raise ValueError("BACKUP_CHANNEL and ORIGIN_CHANNEL must be set in environment variables")

if not api_hash or not api_id:
    raise ValueError("API_HASH and API_ID must be set in environment variables")

# Convert to integers if they are IDs
try:
    backup_channel = int(backup_channel)
    origin_channel = int(origin_channel)

except ValueError:
    pass

app = Client("backupbot", api_id=api_id, api_hash=api_hash)


@app.on(events.NewMessage(outgoing=True, pattern=r"/backup"))
async def backup(events):
    # Get the entities
    backup_entity = await app.get_entity(backup_channel)
    origin_entity = await app.get_entity(origin_channel)

    if backup_channel == events.chat_id:
        print(f"Backup command received, getting messages at {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
        msg = app.iter_messages(entity=origin_entity, reverse=True)
    else:
        print("launched from a different chat that backup channel, ignoring")
        return
    
    messages = []
    async for m in msg:
        if not isinstance(m, MessageService):
            messages.append(m)


    await app.send_message(entity=backup_entity, message=f"Starting backup... {len(messages)} messages to backup")

    total = 0 # Counter to reset the limit of 1500 messages
    for message in messages:
        try:
            await app.send_message(entity=backup_entity, message=message)
            total += 1
            await asyncio.sleep(.5)

            # Reset the counter and wait after 1500 messages
            if total == 1500:
                print("1500 messages limit reached, waiting for 16 minutes;"\
                    f"at {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}")
                await asyncio.sleep(960)  # because floodwait time is around 1000 seconds
                total = 0

        except FloodWaitError as e:
            print(f"FloodWait: Waiting for : {e.seconds}; " \
                f"at {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
            await asyncio.sleep(float(e.seconds))

            await app.send_message(entity=backup_entity, message=message)
            await asyncio.sleep(.5)


print("[Started] Backup bot - waiting for tasks :)")
app.start()
app.run_until_disconnected()