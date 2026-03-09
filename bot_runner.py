import os
import telebot
# Trigger redeploy: 2025-12-27T18:18:00
from dotenv import load_dotenv
from core.db import db
from bot.handlers import register_all_handlers
from bot.reminders import init_reminder_schedule
from bot.backup_scheduler import init_backup_schedule

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
    
    # Fix missing columns (emergency patch)
    print("🔧 Database schema tekshirilmoqda...")
    try:
        from sqlalchemy import create_engine, text
        import os
        engine = create_engine(os.getenv("DATABASE_URL"))
        with engine.connect() as conn:
            # Add streak_workout if missing
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS streak_workout INTEGER DEFAULT 0;
            """))
            # Fix ai_usage_logs user_id to BIGINT if needed
            conn.execute(text("""
                ALTER TABLE ai_usage_logs 
                ALTER COLUMN user_id TYPE BIGINT;
            """))
            conn.commit()
        print("✅ Schema patches applied.")
    except Exception as e:
        print(f"⚠️  Schema patch warning: {e}")
    
    # Run Migrations (Alembic)
    try:
        print("🔄 Migratsiyalar tekshirilmoqda...")
        import subprocess
        # Run "alembic upgrade head"
        # We capture output to avoid spamming logs unless error
        # Run "alembic upgrade head"
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Migratsiyalar muvaffaqiyatli yakunlandi.")
        else:
            print(f"❌ Migratsiya Xatoligi:\n{result.stderr}")
            exit(1) # CRITICAL: Stop the bot if DB is broken to avoid 409 conflicts from zombie containers
            
    except Exception as e:
        print(f"❌ Migratsiya jarayonida xatolik: {e}")
        exit(1)

    # Initialize Database (Sync, legacy check if needed)
    db.init_db()
    print("✅ Database ulandi.")
    
    # Register Handlers
    register_all_handlers(bot)
    print("✅ Handlerlar yuklandi.")
    
    # Initialize Schedules
    init_reminder_schedule(bot)
    init_backup_schedule(bot)
    
    # Start ONE background scheduler thread for ALL jobs
    import schedule
    import time
    import threading
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1) # Reduced to 1s to prevent cumulative drift and missed minute windows

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Background Shceduler (Reminders, Backup, Retention) ishga tushdi.")
    
    # Start Polling
    print("🤖 Bot ishlamoqda...")
    bot.remove_webhook()

    # Set Chat Menu Button (Mini App)
    # Using MINI_APP_URL as the primary source for consistency
    webapp_url = os.getenv("MINI_APP_URL") or os.getenv("WEBAPP_URL")
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

    print("🤖 Bot ishlamoqda...")
    
    # Start Polling with robust restart logic for network issues
    import time
    import signal
    import sys
    from requests.exceptions import ReadTimeout, ConnectionError
    
    # Graceful Shutdown Handler
    def signal_handler(sig, frame):
        print("🛑 To'xtatish signali qabul qilindi (SIGTERM). Bot o'chmoqda...")
        bot.stop_polling()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    
    while True:
        try:
            bot.remove_webhook() # Ensure we are in polling mode
            # Use non_stop=False so that exceptions (like 409) bubble up to our try/except block.
            # infinity_polling swallows them, which prevents our Kill Switch from working.
            bot.polling(non_stop=False, timeout=20, long_polling_timeout=20)
        except (ReadTimeout, ConnectionError) as e:
            print(f"⚠️ Tarmoq xatoligi (qayta ulanish 5s): {e}")
            time.sleep(5)
        except Exception as e:
            # Check for 409 Conflict
            error_str = str(e)
            if "Error code: 409" in error_str:
                print("❌ 409 Conflict detected (Another instance running). Exiting to stop this zombie process.")
                sys.exit(1) # Die immediately so the new container can live
            
            print(f"❌ Kutilmagan xatolik (qayta ulanish 5s): {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
