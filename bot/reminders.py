import time
import threading
import schedule
from datetime import datetime, timedelta, timezone
from core.db import db
from core.coach import get_coach_message
from bot.languages import get_text

# Uzbekistan Timezone (UTC +5)
UZ_TZ = timezone(timedelta(hours=5))

def send_daily_reminders(bot):
    """Batched reminder process with Uzbekistan timezone awareness."""
    now = datetime.now(UZ_TZ)
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    weekday = now.weekday()
    
    # Batch processing to prevent OOM
    BATCH_SIZE = 100
    offset = 0
    total_processed = 0
    
    while True:
        # We need last_checkin for inactivity calculation
        # Let's ensure it's fetched in Batch (updating db.py if needed, or just using current batch)
        # Actually I didn't include it in get_active_users_batch query, let me fix that in db.py first or assume it's there.
        # I added streak_water, streak_workout but forgot last_checkin. 
        # I will fix and then use it.
        users = db.get_active_users_batch(limit=BATCH_SIZE, offset=offset)
        if not users:
            break
            
        for user in users:
            try:
                user_id = user['id']
                full_name = user['full_name']
                # settings already fetched
                settings = user.get('settings', {}) or {}
                
                # --- QUIET HOURS CHECK ---
                # Check current hour in Tashkent time
                hour = now.hour
                is_quiet_hour = (hour >= 23 or hour < 6)
                
                # If it's a quiet hour, we ONLY send if it was explicitly requested for this exact minute
                # (e.g. user set workout at 05:00 for some reason).
                # But for general "Nudges", we skip.

                # Default Settings if empty
                if not settings:
                    settings = {
                        "workoutReminders": True,
                        "workoutTime": "09:00",
                    }

                MSG_SENT = False

                # 1. Workout Reminder (Time based)
                if settings.get("workoutReminders") and settings.get("workoutTime") == current_time:
                     if not db.check_specific_reminder_sent(user_id, today, "workout"):
                        lang = db.get_user_language(user_id)
                        name = full_name if full_name else (user.get('username') or "Aziz foydalanuvchi")
                        
                        # Calculate Inactivity
                        last_checkin_str = user.get('last_checkin')
                        inactivity = 0
                        if last_checkin_str:
                            try:
                                last_date = datetime.strptime(last_checkin_str, "%Y-%m-%d").replace(tzinfo=UZ_TZ)
                                inactivity = (now - last_date).days
                            except: pass

                        # --- COACH ZONE INTEGRATION ---
                        user_context = {
                            "streak_workout": user.get('streak_workout', 0),
                            "streak_water": user.get('streak_water', 0),
                            "inactivity_days": inactivity
                        }
                        
                        coach_result = get_coach_message(user_id, user_context)
                        coach_msg = coach_result[0] if isinstance(coach_result, tuple) else coach_result
                        
                        if coach_msg:
                            msg = f"🧘‍♂️ <b>Coach:</b>\n{coach_msg}"
                            bot.send_message(user_id, msg, parse_mode="HTML")
                        else:
                            msg = "🏋️ " + get_text("reminder_workout_prompt", lang=lang, name=name)
                            bot.send_message(user_id, msg)
                        
                        db.mark_specific_reminder_sent(user_id, today, "workout")
                        MSG_SENT = True

                # 2. General Day Reminder (09:00)
                # Skip if quiet hour (though 09:00 is not quiet)
                if not MSG_SENT and current_time == "09:00" and not is_quiet_hour:
                    if not db.check_reminder_sent(user_id, today):
                        lang = db.get_user_language(user_id)
                        name = full_name if full_name else (user.get('username') or "Aziz foydalanuvchi")
                        # (rest of logic same)
                        weekday = now.weekday()
                        msg = get_text(f"reminder_day_{weekday}", lang=lang, name=name)
                        bot.send_message(user_id, msg)
                        db.mark_reminder_sent(user_id, today)
                        MSG_SENT = True
                
                if MSG_SENT:
                    total_processed += 1
                
                # Mini sleep to prevent API flood limits per second
                time.sleep(0.04) 
                
            except Exception as e:
                print(f"Failed to send reminder to {user.get('id')}: {e}")
                if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                    # Deactivate user to speed up future batches
                    db.update_user_profile(user['id'], active=False)
        
        # Next Batch
        offset += BATCH_SIZE
        
        # Safety break for massive loops (optional)
        if offset > 100000: break 

    if total_processed > 0:
        print(f"[{current_time} UZ] Daily reminders sent to {total_processed} users (Batched).")

def init_reminder_schedule(bot):
    """Initializes the reminder schedule. Runs every minute to check for specific user times."""
    schedule.every(1).minutes.do(send_daily_reminders, bot)
    print("✅ Eslatmalar xizmati rejalashtirildi (Har minutda tekshirish).")
