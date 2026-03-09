import time
import threading
import schedule
from core.db import db

def send_daily_reminders(bot):
    users = db.get_active_users()
    count = 0
    for user in users:
        try:
            user_id = user[0]
            full_name = user[1]
            username = user[2]
            
            name = full_name if full_name else (username if username else "Aziz foydalanuvchi")
            
            msg = f"☀️ Salom {name}! Bugun suv ichdingizmi va mashqlarni qildingizmi? 💧💪\n\n/start tugmasini bosib vazifalarni tekshiring!"
            bot.send_message(user_id, msg)
            count += 1
        except Exception as e:
            print(f"Failed to send reminder to {user[0]}: {e}")
            # Optional: Mark as inactive if blocked
            if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                db.set_user_active(user[0], False)
    
    print(f"Daily reminders sent to {count} users.")

def start_reminder_thread(bot):
    # Schedule daily reminder at 09:00
    schedule.every().day.at("09:00").do(send_daily_reminders, bot)
    
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=run_schedule, daemon=True)
    thread.start()
    print("✅ Eslatmalar xizmati ishga tushdi (09:00).")
