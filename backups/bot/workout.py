from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu
from bot.keyboards import plan_inline_keyboard
from bot.premium import require_premium

# Simple in-memory lock
GENERATION_LOCKS = set()


def handle_plan_menu(message, bot):
    bot.send_message(
        message.chat.id,
        "🏋️ **Mening Rejam**\n\nQaysi reja kerak?",
        reply_markup=plan_inline_keyboard(),
        parse_mode="Markdown"
    )

def handle_workout_plan(message, bot):
    """Entry point for workout plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_workout_template_menu
    show_workout_template_menu(message, bot)

def handle_meal_plan(message, bot):
    """Entry point for meal plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_meal_template_menu
    show_meal_template_menu(message, bot)

@require_premium
def generate_ai_workout(message, bot, user_id=None):
    """Generate AI workout plan (7-Day JSON System)"""
    from core.ai import ai_generate_weekly_workout_json
    import json
    import time
    
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    # 0. Check Limit
    allowed, limit_msg = db.check_ai_gen_limit(user_id, 'workout')
    if not allowed:
        bot.send_message(user_id, limit_msg, parse_mode="Markdown")
        return

    # 0.5 Check Lock
    if user_id in GENERATION_LOCKS:
        bot.send_message(user_id, "⏳ Sabr qiling, reja tuzilmoqda...")
        return
        
    GENERATION_LOCKS.add(user_id)
    try:
    
    # 1. Check if user already has an active workout link
    active_link = db.get_user_workout_link(user_id)
    if active_link:
        # Auto-open today's workout
        show_daily_workout(bot, user_id, active_link)
        return

    # 2. Build Shared Profile Key (Deduplication)
    # Group users by simple age bands to increase matches
    age = user.get('age', 25)
    age_band = "18-25"
    if age > 45: age_band = "46+"
    elif age > 35: age_band = "36-45"
    elif age > 25: age_band = "26-35"
    
    # Key: workout_v2_Gender_Goal_Activity_AgeBand
    profile_key = f"workout_v2_{user.get('gender')}_{user.get('goal')}_{user.get('activity_level')}_{age_band}".replace(" ", "_").lower()

    # 3. Check for Existing Shared Template
    existing_template = db.get_workout_template(profile_key)
    
    if existing_template:
        bot.send_message(user_id, "💡 Sizga mos tayyor reja topildi! Yuklanmoqda...")
        db.create_user_workout_link(user_id, existing_template['id'])
        
        new_link = db.get_user_workout_link(user_id)
        # We assume cached plans are already "valid" usage, or maybe we discount usage? 
        # Requirement says "reuse", implies saving cost.
        # But for logic simplicity, we still count it as a "generation request" fulfilled.
        db.increment_ai_usage(user_id, 'workout') 
        show_daily_workout(bot, user_id, new_link, override_day_idx=1)
        return

    # If no template, generate new
    # If no template, generate new
    msg = bot.send_message(user_id, "⏳ Siz uchun 7 kunlik mashg'ulotlar rejasini tuzyapman... Biroz kuting.")
        
    try:
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            log_ai_usage(bot, user_id, "workout", 2500)
        except: pass

        # Retry Loop for Robustness
        max_retries = 3
        data = None
        
        for attempt in range(max_retries):
            try:
                bot.edit_message_text(f"🧘‍♀️ Siz uchun 7 kunlik mashg'ulotlar rejasini tuzyapman...", user_id, msg.message_id)
                data = ai_generate_weekly_workout_json(user)
                
                if data and 'schedule' in data and isinstance(data['schedule'], list):
                    item_count = len(data['schedule'])
                    
                    if item_count >= 5: # Accept at least 5 days
                        break
                    else:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                            
            except Exception as e:
                print(f"workout_gen_attempt_error: {e}")
                if attempt == max_retries - 1:
                    bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, msg.message_id)
                    return
        
        if not data or 'schedule' not in data:
            bot.edit_message_text(f"❌ AI javob bermadi.", user_id, msg.message_id)
            return

        final_count = len(data['schedule'])
        if final_count < 5:
             bot.edit_message_text(f"❌ Juda qisqa natija ({final_count} kun). Qayta urining.", user_id, msg.message_id)
             return

        bot.edit_message_text("💾 Bazaga saqlanmoqda...", user_id, msg.message_id)
        
        try:
            template_id = db.create_workout_template(
                profile_key,
                json.dumps(data['schedule'])
            )
        except Exception as e:
            # Fallback update
            template_id = db.update_workout_template_content(
                profile_key,
                json.dumps(data['schedule'])
            )
            if not template_id:
                exist = db.get_workout_template(profile_key)
                if exist: template_id = exist['id']
                else: raise e
        
        db.create_user_workout_link(user_id, template_id)
        
        bot.delete_message(user_id, msg.message_id)
        bot.send_message(user_id, "✅ Haftalik mashqlar rejasi tayyor! Marhamat:")
        
        new_link = db.get_user_workout_link(user_id)
        db.increment_ai_usage(user_id, 'workout')
        show_daily_workout(bot, user_id, new_link, override_day_idx=1)
            
    except Exception as e:
        print(f"Main Workout Gen Error: {e}")
        try:
            bot.edit_message_text(f"❌ Katta Xatolik: {str(e)[:100]}", user_id, msg.message_id)
        except:
             pass
    finally:
        if user_id in GENERATION_LOCKS:
            GENERATION_LOCKS.remove(user_id)

def show_daily_workout(bot, user_id, link_data, override_day_idx=None):
    """Render the workout for specific day index."""
    import json
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    start_date = link_data['start_date']
    day_idx = link_data['current_day_index']
    
    # Safe date parsing
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
        except:
             try:
                 start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
             except:
                 start_date = datetime.utcnow()

    # Logic: If no override, use DB value. 
    # (Simplified from menu logic, we trust DB or override)
    if override_day_idx is not None:
        day_idx = override_day_idx
        
    try:
        # Load Workout
        schedule = json.loads(link_data['workout_json'])
        total_days = len(schedule)
        
        # Boundary checks
        if day_idx < 1: day_idx = 1
        if day_idx > total_days: 
            day_idx = total_days
        
        db.update_workout_day(user_id, day_idx)

        # Find day data
        day_data = None
        idx = day_idx - 1
        if 0 <= idx < total_days:
            day_data = schedule[idx]
        
        if not day_data:
            bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
            return

        # Format Message
        # { "day": 1, "focus": "...", "exercises": "..." }
        
        focus_uu = day_data.get('focus', 'Umumiy')
        
        # Helper map to ensure Uzbek (fallback)
        tr_map = {
            "Upper Body": "Yuqori Tana",
            "Lower Body": "Pastki Tana",
            "Full Body": "Butun Tana",
            "Core": "Press / Bel",
            "Cardio": "Kardio",
            "Rest": "Dam olish"
        }
        # If the AI returns English, map it. If it returns Uzbek, keep it.
        final_focus = tr_map.get(focus_uu, focus_uu)
        
        txt = f"🏋️ <b>{day_idx}-KUN</b> (Jami {total_days} kun)\n"
        txt += f"🎯 <b>Fokus:</b> {final_focus}\n\n"
        
        exercises_text = day_data.get('exercises', '-')
        
        # Display the AI-generated HTML directly
        txt += f"{exercises_text}"
        
        # Add visual separator (optional)
        # txt += "\n\n_______________________" # REMOVED per user request
            
        # Buttons
        markup = InlineKeyboardMarkup()
        btns = []
            
        if day_idx > 1:
            btns.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"workout_prev_{day_idx}"))
        
        if day_idx < total_days:
            btns.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"workout_next_{day_idx}"))
            
        markup.row(*btns)
        
        # Regenerate Button
        if day_idx == total_days:
             markup.row(InlineKeyboardButton("🔄 Yangi Reja Tuzish", callback_data="workout_regenerate"))
        else:
             markup.row(InlineKeyboardButton("🔄 Yangilash (Reset)", callback_data="workout_regenerate"))
        
        bot.send_message(user_id, txt, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

    except Exception as e:
        print(f"Show Workout Error: {e}")
        bot.send_message(user_id, "❌ Mashqni ochishda xatolik.")

from bot.premium import require_premium

@require_premium
def generate_ai_meal(message, bot, user_id=None):
    """Generate AI meal plan (Monthly Menu System)"""
    from core.ai import ai_generate_monthly_menu_json
    import json
    import time
    
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    # 0. Check Limit
    allowed, limit_msg = db.check_ai_gen_limit(user_id, 'menu')
    if not allowed:
        bot.send_message(user_id, limit_msg, parse_mode="Markdown")
        return

    # 0.5 Check Lock
    if user_id in GENERATION_LOCKS:
        bot.send_message(user_id, "⏳ Sabr qiling, reja tuzilmoqda...")
        return

    GENERATION_LOCKS.add(user_id)
    try:
    
    # 1. Check if user already has an active menu link
    # RESTORED: Check for regular users
    active_link = db.get_user_menu_link(user_id)
    if active_link:
        # Auto-open today's menu
        show_daily_menu(bot, user_id, active_link)
        return

    # 2. Build Shared Profile Key (Deduplication)
    age = user.get('age', 25)
    age_band = "18-25"
    if age > 45: age_band = "46+"
    elif age > 35: age_band = "36-45"
    elif age > 25: age_band = "26-35"
        
    profile_key = f"menu_v2_{user.get('gender')}_{user.get('goal')}_{user.get('activity_level')}_{user.get('allergies')}_{age_band}".replace(" ", "_").lower()
    
    # 3. Check for Existing Shared Template
    existing_template = db.get_menu_template(profile_key)
    
    if existing_template:
        bot.send_message(user_id, "💡 Sizga mos tayyor menyu topildi! Yuklanmoqda...")
        db.create_user_menu_link(user_id, existing_template['id'])
        
        new_link = db.get_user_menu_link(user_id)
        db.increment_ai_usage(user_id, 'menu')
        show_daily_menu(bot, user_id, new_link, override_day_idx=1)
        return

    # If no template, generate new
    # If no template, generate new
    msg = bot.send_message(user_id, "🚀 **Jarayon boshlandi...**\n\n🥗 Siz uchun 7 kunlik ovqatlanish menyusini tuzyapman...", parse_mode="Markdown")
        
    # [SAFE LOGGING ADDITION]
    try:
        from core.ai_usage_logger import log_ai_usage
        log_ai_usage(bot, user_id, "menu", 2000)
    except: pass
        
    try:
        # Retry Loop for Robustness (Force 30 days)
        max_retries = 3
        data = None
        
        for attempt in range(max_retries):
            try:
                bot.edit_message_text(f"🥗 Siz uchun 7 kunlik ovqatlanish menyusini tuzyapman...", user_id, msg.message_id)
                data = ai_generate_monthly_menu_json(user)
                
                if data and 'menu' in data and isinstance(data['menu'], list):
                    item_count = len(data['menu'])
                    
                    if item_count >= 7: 
                        break
                    else:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                            
            except Exception as e:
                print(f"gen_attempt_error: {e}")
                if attempt == max_retries - 1:
                    bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, msg.message_id)
                    return
        
        if not data or 'menu' not in data:
            bot.edit_message_text("❌ AI javob bermadi.", user_id, msg.message_id)
            return

        final_count = len(data['menu'])
        if final_count < 5:
             bot.edit_message_text(f"❌ Juda qisqa natija ({final_count} kun). Qayta urining.", user_id, msg.message_id)
             return

        bot.edit_message_text("💾 Bazaga saqlanmoqda...", user_id, msg.message_id)
        
        try:
            template_id = db.create_menu_template(
                profile_key,
                json.dumps(data['menu']),
                json.dumps(data['shopping_list'])
            )
        except Exception as e:
            # Fallback update
            template_id = db.update_menu_template_content(
                profile_key,
                json.dumps(data['menu']),
                json.dumps(data['shopping_list'])
            )
            if not template_id:
                exist = db.get_menu_template(profile_key)
                if exist: template_id = exist['id']
                else: raise e
        
        db.create_user_menu_link(user_id, template_id)
        
        bot.delete_message(user_id, msg.message_id)
        bot.send_message(user_id, "✅ Haftalik reja tayyor! Marhamat:")
        
        new_link = db.get_user_menu_link(user_id)
        db.increment_ai_usage(user_id, 'menu')
        show_daily_menu(bot, user_id, new_link, override_day_idx=1)
            
    except Exception as e:
        print(f"Main Gen Error: {e}")
        try:
            bot.edit_message_text(f"❌ Katta Xatolik: {str(e)[:100]}", user_id, msg.message_id)
        except:
        except:
             pass
    finally:
        if user_id in GENERATION_LOCKS:
            GENERATION_LOCKS.remove(user_id)

def get_weekday_name(date_obj):
    # 0=Mon, ... 3=Thu ...
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    return days[date_obj.weekday()]

def show_daily_menu(bot, user_id, link_data, override_day_idx=None):
    """Render the menu for specific day index. 
    If override_day_idx is None, calculates based on date logic (Auto-progression).
    """
    import json
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    start_date = link_data['start_date'] # datetime object or string
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
        except:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            except:
                start_date = datetime.utcnow() # Fallback
    
    # Logic: If no override, calculate specific day
    if override_day_idx is None:
        today = datetime.utcnow() # Assuming start_date is UTC
        # Calculate difference + 1
        # If start_date is today, diff is 0 days, so Day 1.
        delta = today - start_date
        real_day_idx = delta.days + 1
        
        # Cap logic if needed, or if plan expired
        # If real_day_idx > 30, we can say "Finish" or just show 30.
        # Let's show proper day
        day_idx = real_day_idx
    else:
        day_idx = override_day_idx
        
    try:
        # Load Menu
        menu_list = json.loads(link_data['menu_json'])
        total_days = len(menu_list)
        
        # Boundary checks
        clamped = False
        if day_idx < 1: day_idx = 1
        if day_idx > total_days: 
            day_idx = total_days # Stop at last day
            clamped = True
        
        # Calculate Display Date for the *viewed* day
        current_view_date = start_date + timedelta(days=day_idx-1)
        # viewed_date = start_date + (day_idx - 1) days
        current_view_date = start_date + timedelta(days=day_idx-1)
        weekday_name = get_weekday_name(current_view_date)
        date_str = current_view_date.strftime("%d.%m.%Y")
        
        # Build Text
        txt = f"📅 **{day_idx}-KUN** (Jami {total_days} kun) | {weekday_name}, {date_str}\n\n"
        
        if clamped:
             txt += f"⚠️ **DIQQAT:** Sizning rejangiz jami {total_days} kunlik. Davom etish uchun yangi reja tuzing.\n\n"
             
        db.update_menu_day(user_id, day_idx)

        # Find day data
        day_data = None
        # menu_list is 0-indexed, day_idx is 1-indexed
        idx = day_idx - 1
        if 0 <= idx < total_days:
            day_data = menu_list[idx]
        
        if not day_data:
            bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
            return

        # Format Message
        # txt is already started
        txt += f"🍳 **Nonushta:**\n{day_data.get('breakfast', '-')}\n\n"
        txt += f"🥗 **Tushlik:**\n{day_data.get('lunch', '-')}\n\n"
        txt += f"🍲 **Kechki ovqat:**\n{day_data.get('dinner', '-')}\n\n"
        txt += f"🍏 **Snack:**\n{day_data.get('snack', '-')}\n"
            
        # Buttons
        markup = InlineKeyboardMarkup()
        btns = []
            
        if day_idx > 1:
            btns.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"menu_prev_{day_idx}"))
        
        if day_idx < total_days:
            btns.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"menu_next_{day_idx}"))
        elif day_idx == total_days: # End of current plan (e.g. Day 7)
            # Show "Generate Next Week" button
            btns.append(InlineKeyboardButton("Keyingi Hafta (Yangi) 🔄", callback_data="menu_regenerate"))
            
        markup.row(*btns)
        
        # Add Shopping List and Regenerate Buttons
        markup.row(InlineKeyboardButton("🛒 Xaridlar ro'yxati", callback_data="menu_shopping"))
        if day_idx < total_days:
             markup.row(InlineKeyboardButton("🔄 Haftani Yangilash (Reset)", callback_data="menu_regenerate"))
        
        bot.send_message(user_id, txt, parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        print(f"Show Menu Error: {e}")
        bot.send_message(user_id, "❌ Menyu ochishda xatolik.")
