import os
import telebot
from dotenv import load_dotenv
from core.db import db
from bot.handlers import register_all_handlers
from bot.reminders import start_reminder_thread

from telebot import apihelper

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in .env file.")
    exit(1)

# Enable Middleware
apihelper.ENABLE_MIDDLEWARE = True

# Initialize Bot
bot = telebot.TeleBot(BOT_TOKEN, num_threads=5)

def main():
    print("🚀 Fitness AI Bot ishga tushmoqda...")
    
    # Initialize Database
    db.init_db()
    print("✅ Database ulandi.")
    
    # Register Handlers
    register_all_handlers(bot)
    print("✅ Handlerlar yuklandi.")
    
    # Start Reminder Thread
    start_reminder_thread(bot)
    print("✅ Eslatmalar xizmati ishga tushdi.")
    
    # Start Polling
    print("🤖 Bot ishlamoqda...")
    bot.remove_webhook()

    # Set Chat Menu Button (Mini App)
    webapp_url = os.getenv("WEBAPP_URL")
    if webapp_url:
        try:
            bot.set_chat_menu_button(
                menu_button=telebot.types.MenuButtonWebApp(
                    type="web_app", 
                    text="📱 Ilova", 
                    web_app=telebot.types.WebAppInfo(url=webapp_url)
                )
            )
            print(f"✅ Menu tugmasi o'rnatildi: {webapp_url}")
        except Exception as e:
            print(f"⚠️ Menu tugmasini o'rnatishda xatolik: {e}")
    else:
        print("⚠️ WEBAPP_URL topilmadi. Mini App tugmasi o'rnatilmadi.")

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot to‘xtadi: {e}")

if __name__ == "__main__":
    main()
