import telebot
import os
import time
from dotenv import load_dotenv

from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(env_path)
print(f"Loading env from: {env_path}")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in .env")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

print("🤖 Bot ID oluvchi skript ishga tushdi...")
print("1. Botni kanalingizga admin qiling.")
print("2. Kanalga biron xabar yozing (masalan: 'test').")
print("3. Men ID ni shu yerda chiqaraman.")
print("Waiting for updates...")

offset = None
while True:
    try:
        updates = bot.get_updates(offset=offset, timeout=10)
        for u in updates:
            offset = u.update_id + 1
            
            # Check channel post
            if u.channel_post:
                chat = u.channel_post.chat
                print(f"\n✅ KANAL TOPILDI!\nNom: {chat.title}\nID: {chat.id}\nUsername: @{chat.username}\n")
                print(f"👉 .env fayliga qo'shing:\nVIDEO_DB_CHANNEL_ID={chat.id}")
                exit(0)
            
            # Check message forwarding (if user forwards from channel)
            if u.message and u.message.forward_from_chat:
                chat = u.message.forward_from_chat
                print(f"\n✅ KANAL (Forward) TOPILDI!\nNom: {chat.title}\nID: {chat.id}\n")
                exit(0)
                
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
