import asyncio
from datetime import datetime
import json
import logging
import os


from dotenv import load_dotenv
from telethon import events, TelegramClient as Client
from telethon.tl.types import MessageService
from telethon.errors import FloodWaitError, FileReferenceExpiredError


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING)

load_dotenv(dotenv_path = ".token/token.env")

api_hash = os.getenv("API_HASH")
api_id = os.getenv("API_ID")
bot_token = os.getenv("BOT_TOKEN")

if not api_hash or not api_id:
    raise ValueError("API_HASH and API_ID must be set in environment variables")

app = Client("backupbot", api_id=api_id, api_hash=api_hash)

async def save_data(origin_channel:str, last_id:int):
    with open("backup_data.json", "r") as f:
            channel_data = json.load(f)
    
    channel_data[str(origin_channel)]["last_id"] = last_id

    with open("backup_data.json", "w") as f:
        json.dump(channel_data, f, indent=4)

async def backup_messages(origin_channel, backup_channel, last_id:int):
    try:
        backup_entity = await app.get_entity(backup_channel)
        origin_entity = await app.get_entity(origin_channel)

        async def fetch_messages(last_id: int):
            messages = []
            async for m in app.iter_messages(origin_entity, min_id=last_id, reverse=True):
                if not isinstance(m, MessageService):
                    messages.append(m)

            print(f"Backup de {len(messages)} messages...")
            return messages
        
        messages = await fetch_messages(last_id=last_id)
        if not messages:
            print("Aucun message à sauvegarder.")
            return

        total = 0
        for message in messages[:-1]:
            try:
                await app.send_message(backup_entity, message)
                total += 1
                await asyncio.sleep(0.5)

                if total % 500 == 0:
                    await save_data(str(origin_channel), message.id)
                    print(f"500 messages envoyés, pause de 05 min...")
                    await asyncio.sleep(300)

            except FloodWaitError as e:
                await save_data(str(origin_channel), message.id)
                print(f"FloodWait: Attente de {e.seconds}s...")
                await asyncio.sleep(e.seconds + 10)

            except FileReferenceExpiredError:
                await save_data(str(origin_channel), message.id)
                print("Fichier expiré, récuperation d'une liste actualisée après une pause de 5min.")
                await asyncio.sleep(300)
                messages = fetch_messages(last_id=message.id)
                continue

            except Exception as e:
                print(f"Erreur: {e}, attente de 10s...")
                await asyncio.sleep(10)
                continue

        await save_data(str(origin_channel), messages[-1].id)

    except Exception as e:
        print(f"Erreur: {str(e)}")

# Dictionary for temporary storage of user states; so as not to overwrite an older configuration.
user_states = {}

@app.on(events.NewMessage(outgoing=True, pattern=r"/backup"))
async def backup_handler(event):
    try:
        with open("backup_data.json", "r") as f:
            channel_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        channel_data = {}
    
    origin_channel = str(event.chat_id)

    if origin_channel not in channel_data:
        print("Envoyer le message /source dans le canal de backup.")
        user_states[origin_channel] = {"waiting_for_source": True,
                                       "origin_channel": str(event.chat_id)}

        if event.is_channel:
            chat = await event.get_chat()
            if chat.username:
                user_states[origin_channel] = {"channel_title": f"@{chat.username}"}
            else:
                user_states[origin_channel] = {"channel_title": f"{chat.title}"}
               
        await event.delete()
        return
    
    last_id = channel_data[origin_channel]["last_id"]
    backup_channel = channel_data[origin_channel]["backup_channel"]
    origin_channel = int(event.chat_id)

    await event.delete()

    print(f"Lancement du backup... à {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}")
    await backup_messages(origin_channel=origin_channel, backup_channel=backup_channel, last_id=last_id)
    print(f"Backup terminé à {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")


@app.on(events.NewMessage(outgoing=True, pattern=r"/source"))
async def set_source_channel(event):
    
    # Check if there was an instance waiting to be configured
    origin_channel = next(iter(user_states.keys()))
    config = user_states[origin_channel]

    if not config.get("waiting_for_source"):
        try:
            with open("backup_data.json", "r") as f:
                channel_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            channel_data = {}

        backup_channel = event.chat_id
        channel_title = config.get("channel_title", "")
        #origin_channel = config.get("origin_channel")

        channel_data[origin_channel] = {
            "last_id": 0,
            "backup_channel": backup_channel,
            "channel_title": channel_title 
        }

        with open("backup_data.json", "w") as f:
            json.dump(channel_data, f, indent=4)
        
        # Clean states
        user_states.clear()

    else:
        await event.reply(
            "Pour configurer un canal source, commencez par envoyer /backup dans le canal que vous voulez backup")

async def main():
    async with app:
        if not await app.is_user_authorized():
            print("Session invalide. Veuillez vous reconnecter.")
            return
        print("Bot en attente...")
        await app.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())