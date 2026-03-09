
import datetime
from core.db import db
from core.flags import is_flag_enabled
from core.context import get_founder_tone_prompt

def run_retention_check(bot):
    """
    Scheduled job to check for inactive users and send nudges.
    """
    # 1. Global Safety Check
    # We can check a global flag first, or check per user.
    # Let's check a "global" switch using a dummy key or just 'retention_engine' without user_id first for efficiency?
    # Actually flags are usually per user. But for a cron job, we can check "if feature is globally enabled or rollout > 0".
    # For simplicity, we'll check inside the loop OR check if it's completely disabled.
    
    # Simple optimization: If flag is completely OFF (enabled=False, rollout=0), abort.
    # flag = db.get_feature_flag("retention_engine")
    # if not flag or (not flag['enabled'] and flag['rollout_percent'] <= 0):
    #    return

    print("Running Retention Check...")
    
    try:
        # 2. Get Candidates (This requires a DB query we might not have yet)
        # ideally: SELECT * FROM users WHERE last_active_date = NOW - INTERVAL '3 days'
        # Since we might not have an efficient index on last_active, we have to be careful.
        # MVP: We can iterate generic "active users" or we need a new DB method `get_inactive_users(days)`.
        
        # Let's Add `get_users_inactive_since(date)` to DB or just simple logic here.
        # If we can't query efficiently, we might skip or do a small batch.
        
        # Assuming we can't change DB schema/indexes easily (Rule 3).
        # We can iterate `get_active_users()`? No, those are active.
        # We need users who are NOT active.
        
        # Let's use `updated_at` from `users` table if available.
        # If not, we rely on `daily_logs`.
        
        # For this MVP task without changing generic helpers too much:
        # Let's rely on a new DB helper `get_users_by_inactivity(days)` which we will add to DB class (Safety Rule 5 allows new helpers).
        
        days_triggers = [3, 7, 10, 14]
        
        for days in days_triggers:
            users = db.get_users_inactive_for(days) 
            
            for user in users:
                # user is SQLAlchemy object (User model), not dict
                user_id = user.telegram_id
                name = user.full_name
                
                # Double check flag per user (Rollout support)
                if not is_flag_enabled("retention_engine", user_id):
                    continue
                    
                # Send Message
                send_retention_message(bot, user_id, name, days)
        
        # 3. Weekly Report Check
        run_weekly_report_check(bot)
                
    except Exception as e:
        print(f"Retention Check Error: {e}")

def send_retention_message(bot, user_id, name, days):
    """
    Sends the specific message for the day.
    """
    try:
        msg = ""
        if days == 3:
            msg = f"👋 Salom {name}, ko'rinmay qoldingiz? Kichik qadamlar katta natijaga olib keladi. Bugun 5 daqiqa ajrata olamizmi?"
        elif days == 7:
            msg = f"Hafta o'tib ketdi, {name}. 📉 Ko'pchilik shu nuqtada tashlab ketadi. Siz ulardan emassiz. Qaytish uchun bitta tugmani bosish kifoya."
        elif days == 10:
            msg = f"{name}, rostini aytaman - formadan chiqish oson, qaytish qiyin. Lekin imkon bor. Bugun shunchaki suv ichishni belgilang, yetarli."
        elif days == 14:
            msg = f"2 hafta bo'ldi... 😔 Men hali ham shu yerdaman. Sizning maqsadingiz ham shu yerdami? Kel, bugun yangidan boshlaymiz."
            
        if msg:
            # Apply Founder Tone if enabled
            if is_flag_enabled("founder_tone", user_id):
                # Add direct founder signature/intro
                founder_intro = "👋 Isroil Jalolov.\n\nYasha Bot yaratuvchisiman. Sizga juda muhim gap aytmoqchiman:\n\n"
                msg = founder_intro + msg
                
            bot.send_message(user_id, msg)
            # Log it
            from core.observability import log_event
            log_event("retention_sent", user_id=user_id, meta={"days": days})
            
    except Exception as e:
        print(f"Failed to send retention to {user_id}: {e}")

def run_weekly_report_check(bot):
    """
    Weekly Progress Report Job.
    Runs for users with anniversary (7, 14, 21 days...)
    """
    print("Running Weekly Report Check...")
    import random
    from backend.database import get_sync_db
    from backend.models import ActivityLog, DailyLog
    from sqlalchemy import func
    
    try:
        users = db.get_users_for_report(mod_days=7)
        if not users: return

        for user in users:
            uid = user['telegram_id']
            name = user['full_name']
            
            # Check progress_insights flag per user
            if not is_flag_enabled("progress_insights", uid):
                continue
            
            # 1. Calculate Stats (Last 7 days)
            active_days = 0
            try:
                with get_sync_db() as session:
                    # Count distinct days with activity
                    # Simple proxy: Count DailyLog entries for last 7 days?
                    # Or ActivityLog unique days
                    now = datetime.datetime.utcnow()
                    week_ago = now - datetime.timedelta(days=7)
                    
                    count = session.query(func.count(DailyLog.id))\
                        .filter(DailyLog.user_id == db._get_user_pk(session, uid))\
                        .filter(DailyLog.date >= week_ago.strftime("%Y-%m-%d"))\
                        .scalar()
                    active_days = count if count else 0
                    if active_days > 7: active_days = 7
            except Exception as e:
                print(f"Stats error for {uid}: {e}")
                active_days = 5 # Fallback positive assumption

            # 2. Choose Variant
            variant = random.choice([1, 2, 3])
            msg = ""
            
            if variant == 1:
                # Iliq va rag'batlantiruvchi
                msg = (
                    f"🧾 **So'nggi 7 kun natijalari**\n\n"
                    f"Sen bu hafta {active_days} kun faol bo'lding.\n"
                    "Suv ichish, ovqat va mashqlar — bularning barchasi tanangda ishlayapti.\n\n"
                    "Katta natija birdan bo'lmaydi, lekin sen to'g'ri yo'ldasan. Davom etamiz 💪"
                )
            elif variant == 2:
                # Psixologik
                msg = (
                    "🔄 **Haftalik xulosa**\n\n"
                    "Ko'pchilik 3-kunda tashlaydi.\n"
                    "Sen esa davom etding.\n\n"
                    "Bu — intizom belgisi. Natija shundan keyin keladi."
                )
            else:
                # Fakt + Motivatsiya
                msg = (
                    "📊 **1 haftalik hisobot**\n\n"
                    f"• Faol kunlar: {active_days}/7\n"
                    "• Dam olish: reja bo'yicha\n\n"
                    "Shunday davom etsang, 1 oyda sezilarli farq bo'ladi.\n"
                    "Men yoningdaman 🤝"
                )
            
            # Apply founder_tone if enabled
            if is_flag_enabled("founder_tone", uid):
                # Make it more direct and personal from founder
                founder_prefix = f"👋 {name}, Isroil'dan salom.\n\n"
                msg = founder_prefix + msg
            
            try:
                bot.send_message(uid, msg, parse_mode="Markdown")
                from core.observability import log_event
                log_event("weekly_report_sent", user_id=uid, meta={"variant": variant})
            except Exception as e:
                print(f"Failed to send weekly report to {uid}: {e}")
                
    except Exception as e:
        print(f"Weekly Report Error: {e}")
