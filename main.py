import discord
import random
import asyncio
from collections import deque
import aiohttp
import json

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
TOKEN = config["token"]
MESSAGES_FILE = "beef.txt"

used_messages = set()
beef_lines = []
shuffled_beef_lines = deque()
last_sent = None
is_running = False
current_channel_id = None
session = None

stam_running = False
stam_task = None

def load_messages():
    global beef_lines
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            beef_lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        beef_lines = []

def shuffle_lines():
    global shuffled_beef_lines
    global last_sent
    while True:
        temp = deque(sorted(beef_lines, key=lambda x: random.random()))
        if len(beef_lines) <= 1 or temp[0] != last_sent:
            shuffled_beef_lines = temp
            break

async def send_autobeef(client):
    global is_running
    global last_sent
    global used_messages
    global current_channel_id

    channel = client.get_channel(current_channel_id)
    if not channel:
        is_running = False
        return

    channel_name = channel.name if hasattr(channel, 'name') else str(current_channel_id)
    print(f"[INFO] Started autobeefing in {channel_name}")

    while is_running:
        if len(shuffled_beef_lines) == 0:
            if len(beef_lines) == 0:
                is_running = False
                break
            shuffle_lines()

        final_message = None
        max_tries = max(len(shuffled_beef_lines), len(beef_lines), 1)

        for _ in range(max_tries):
            if len(shuffled_beef_lines) == 0:
                break
            candidate = shuffled_beef_lines.pop()
            if candidate not in used_messages:
                final_message = candidate
                last_sent = candidate
                used_messages.add(candidate)
                break

        if not final_message:
            delay = random.uniform(1200, 2500) / 1000
            await asyncio.sleep(delay)
            continue

        delay_typing = random.uniform(1200, 2500) / 1000
        retries = 0
        while retries < 3:
            try:
                async with channel.typing():
                    await asyncio.sleep(delay_typing)
                    await channel.send(final_message)
                break
            except Exception as e:
                if "rate limit" in str(e).lower():
                    retries += 1
                    print(f"[RATE LIMITED] Retrying {retries}/3...")
                    await asyncio.sleep(1.5)
                    if retries == 3:
                        print(f"[RATE LIMITED] Max retries reached, skipping message.")
                else:
                    break

async def stam_loop(client, channel_id, base_message):
    global stam_running
    channel = client.get_channel(channel_id)
    if not channel:
        stam_running = False
        return
    counter = 1
    channel_name = channel.name if hasattr(channel, 'name') else str(channel_id)
    print(f"[INFO] Started stam in {channel_name}")
    while stam_running:
        try:
            message = f"{base_message} ({counter})"
            await channel.send(message)
            counter += 1
            await asyncio.sleep(1.5)
        except Exception as e:
            if "rate limit" in str(e).lower():
                print(f"[RATE LIMITED] Stam: {e}")
                await asyncio.sleep(2)
            pass

client = discord.Client(chunk_guilds_at_startup=False)

@client.event
async def on_ready():
    print(f"[INFO] Logged in as {client.user}")
    load_messages()

@client.event
async def on_message(message):
    global is_running
    global current_channel_id
    global used_messages
    global shuffled_beef_lines
    global last_sent
    global stam_running
    global stam_task

    if message.author.id != client.user.id:
        return
    if not message.content.startswith("!"):
        return
    args = message.content[1:].split()
    if not args:
        return
    command = args.pop(0).lower()
    if command == "ab":
        if not args:
            return
        try:
            channel_id = int(args[0])
        except:
            return
        if is_running:
            return
        used_messages = set()
        shuffled_beef_lines = deque()
        last_sent = None
        current_channel_id = channel_id
        is_running = True
        asyncio.create_task(send_autobeef(client))
    elif command == "sab":
        if not is_running:
            return
        is_running = False
        used_messages = set()
        print("[INFO] Stopped autobeefing")
    elif command == "stam":
        content = message.content[len("!stam "):]
        if not content:
            return
        first_space = content.find(" ")
        if first_space == -1:
            return
        try:
            channel_id = int(content[:first_space])
        except:
            return
        base_message = content[first_space+1:]
        if stam_running:
            return
        stam_running = True
        stam_task = asyncio.create_task(stam_loop(client, channel_id, base_message))
    elif command == "cs":
        if not stam_running:
            return
        stam_running = False
        if stam_task:
            stam_task.cancel()
            stam_task = None
        print("[INFO] Stopped stam")

async def main():
    global session
    session = aiohttp.ClientSession()
    try:
        await client.start(TOKEN)
    finally:
        await session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
