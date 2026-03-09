from telebot import types
from core.db import db
from core.ai import ai_provide_psychological_support
from core.utils import parse_callback
from datetime import datetime

# States for inputs (Must be Integers to match User.onboarding_state)
STATE_STEPS_INPUT = 101
STATE_SLEEP_INPUT = 102
STATE_MOOD_REASON = 103

# --- Water Tracker ---
def handle_water_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
        
    today = datetime.now().strftime("%Y-%m-%d")
    log = db.get_daily_log(user_id, today)
    current_ml = log.get('water_ml', 0) if log else 0
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💧 250ml ichdim", callback_data="track_water_250"))
    
    user = db.get_user(user_id)
    streak = user.get('streak_water', 0)
    
    bot.send_message(
        user_id,
        f"💧 **Suv Balansi**\n\n"
        f"Bugungi maqsadingiz: 2500 ml\n"
        f"Ichildi: {current_ml} ml\n"
        f"🔥 Uzluksiz: {streak} kun\n\n"
        f"Suv ichdingizmi? Belgilang:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def process_water_callback(call, bot):
    user_id = call.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Update log
    log = db.get_daily_log(user_id, today)
    current_ml = log.get('water_ml', 0) if log else 0
    new_ml = current_ml + 250
    
    db.update_daily_log(user_id, today, water_ml=new_ml)
    
    msg_text = f"✅ Qabul qilindi! ({new_ml}/2500 ml)"
    
    # Check for daily goal reward (once per day)
    # We need a flag to know if reward was already given. 
    # For simplicity, we check if we JUST crossed the threshold.
    if current_ml < 2500 and new_ml >= 2500:
        db.update_streak(user_id, 'water') # Increment streak
        db.add_points(user_id, 1)
        msg_text += "\n🎉 Kunlik reja bajarildi! +1 ball"
    
    bot.answer_callback_query(call.id, msg_text)
    
    # Update message
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💧 250ml ichdim", callback_data="track_water_250"))
    
    user = db.get_user(user_id)
    streak = user.get('streak_water', 0)
    
    bot.edit_message_text(
        f"💧 **Suv Balansi**\n\n"
        f"Bugungi maqsadingiz: 2500 ml\n"
        f"Ichildi: {new_ml} ml\n"
        f"🔥 Uzluksiz: {streak} kun\n\n"
        f"Suv ichdingizmi? Belgilang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# --- Steps Tracker ---
def handle_steps_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
        
    from bot import onboarding
    onboarding.manager.set_state(user_id, STATE_STEPS_INPUT)
    
    bot.send_message(
        user_id,
        "🚶 **Qadamlar**\n\nBugun qancha qadam yurdingiz? (Raqam kiriting)\n\n"
        "Har 10,000 qadam uchun 5 ball beriladi! 🎁",
        parse_mode="Markdown"
    )

def process_steps_input(message, bot):
    user_id = message.from_user.id
    
    if not message.text:
        bot.send_message(user_id, "Iltimos, faqat raqam yozing.")
        return

    text = message.text.strip()
    
    if not text.isdigit():
        bot.send_message(user_id, "Iltimos, faqat raqam kiriting.")
        return
        
    steps = int(text)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch previous log to check if points already awarded
    log = db.get_daily_log(user_id, today)
    reward_claimed = log.get('steps_reward_claimed', False) if log else False
    
    # Update steps count regardless
    db.update_daily_log(user_id, today, steps=steps)
    
    # Logic: 10,000 steps = 10 points (Once per day)
    if steps >= 10000:
        if not reward_claimed:
            # First time crossing 10k today
            db.add_points(user_id, 10)
            db.update_daily_log(user_id, today, steps_reward_claimed=True)
            
            msg = f"🎉 **Tabriklaymiz!**\n\nSiz {steps} qadam yurdingiz va kunlik marrani bajardingiz!\n"
            msg += f"✅ **+10 ball berildi**"
            bot.send_message(user_id, msg, parse_mode="Markdown")
        else:
            # Already claimed
            bot.send_message(user_id, f"✅ Qabul qilindi: {steps} qadam.\nSiz bugungi kunlik mukofotni olib bo'lgansiz. Ertaga ko'rishguncha! 💪")
    else:
        # Less than 10k
        bot.send_message(user_id, f"✅ Qabul qilindi: {steps} qadam.\n10,000 ga yetkazishga harakat qiling! (Mukofot: 10 ball) 💪")
        
    from bot import onboarding
    onboarding.manager.clear_user(user_id)

# --- Sleep Tracker ---
def handle_sleep_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
        
    from bot import onboarding
    onboarding.manager.set_state(user_id, STATE_SLEEP_INPUT)
    
    bot.send_message(
        user_id,
        "🌙 **Uyqu Monitoringi**\n\nBugun necha soat uxladingiz? (Raqam kiriting, masalan: 7.5)",
        parse_mode="Markdown"
    )

def process_sleep_input(message, bot):
    user_id = message.from_user.id
    
    if not message.text:
         bot.send_message(user_id, "Iltimos, uxlagan vaqtingizni yozing (masalan 7.5).")
         return

    text = message.text.strip().replace(',', '.')
    
    try:
        hours = float(text)
    except ValueError:
        bot.send_message(user_id, "Iltimos, to'g'ri raqam kiriting.")
        return
        
    today = datetime.now().strftime("%Y-%m-%d")
    # Fetch previous log
    log = db.get_daily_log(user_id, today)
    old_sleep = log.get('sleep_hours', 0) if log else 0
    
    db.update_daily_log(user_id, today, sleep_hours=hours)
    
    if old_sleep < 8 and hours >= 8:
        db.add_points(user_id, 2)
        db.update_streak(user_id, 'sleep') 
        bot.send_message(user_id, f"✅ **Ajoyib uyqu!**\n\nSiz {hours} soat uxladingiz.\nSog'lom uyqu uchun +2 ball! 😴✨", parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"✅ Qabul qilindi: {hours} soat.\nSog'lom bo'lish uchun kamida 8 soat uxlashga harakat qiling.")
        
    from bot import onboarding
    onboarding.manager.clear_user(user_id)

# --- Mood Tracker ---
def handle_mood_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("😞 Yomon", callback_data="track_mood_bad"),
        types.InlineKeyboardButton("😐 O'rtacha", callback_data="track_mood_ok"),
        types.InlineKeyboardButton("😊 A'lo", callback_data="track_mood_good")
    )
    
    bot.send_message(
        user_id,
        "🧠 **Kayfiyat Kundaligi**\n\nBugun o'zingizni qanday his qilyapsiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )


def process_mood_callback(call, bot): # keys: track_mood_
    user_id = call.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")

    parts = parse_callback(call.data, prefix="track_mood_", min_parts=3)
    
    if not parts:
        bot.answer_callback_query(call.id, "Xatolik")
        return

    try:
        mood = parts[2] # bad, ok, good
        
        # Check previous mood to prevent double points
        log = db.get_daily_log(user_id, today)
        old_mood = log.get('mood') if log else None
        
        db.update_daily_log(user_id, today, mood=mood) 
        
        if mood == 'good' and old_mood != 'good':
            db.add_points(user_id, 5) 
            db.update_streak(user_id, 'mood')
            bot.answer_callback_query(call.id, "✅ Ajoyib! +5 ball")
            bot.edit_message_text(
                "✅ **Kayfiyat a'lo!**\nShunday davom eting! ✨",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        elif mood == 'good' and old_mood == 'good':
             bot.answer_callback_query(call.id, "Bugun allaqachon belgilagansiz 🙂")
             # Don't edit message to avoid flicker or just leave it
        
            
        elif mood == 'bad':
            from bot import onboarding
            onboarding.manager.set_state(user_id, STATE_MOOD_REASON)
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                "😔 **Tushunaman...**\n\nNega kayfiyatingiz yomon? Qisqacha yozib yuboring, balki yordam bera olarman.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        else: # mood == 'ok'
            bot.answer_callback_query(call.id, "✅ Qabul qilindi")
            bot.edit_message_text(
                "✅ **Kayfiyat o'rtacha.**\nYaxshi dam olishga harakat qiling!",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        print(f"Mood track error: {e}")
        bot.answer_callback_query(call.id, "Xatolik")

def process_mood_reason(message, bot):
    user_id = message.from_user.id
    
    if not message.text:
        bot.send_message(user_id, "Iltimos, sababni matn ko'rinishida yozing.")
        return

    reason = message.text
    today = datetime.now().strftime("%Y-%m-%d")
    
    db.update_daily_log(user_id, today, mood_reason=reason)
    
    # Log as a problem for easier tracking
    db.log_activity(user_id, "problem", f"Mood Reason: {reason}")
    
    # AI Support
    bot.send_chat_action(user_id, 'typing')
    support_msg = ai_provide_psychological_support(reason)
    
    bot.send_message(user_id, support_msg, parse_mode="HTML")
    
    from bot import onboarding
    onboarding.manager.clear_user(user_id)

# --- Main Habits Menu ---
from bot.keyboards import habits_inline_keyboard

def handle_habits_menu(message, bot):
    with open("assets/kunlik_odatlar.png", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption="🔁 **Odatlar**\n\nQaysi odatni kiritmoqchisiz?",
            reply_markup=habits_inline_keyboard(),
            parse_mode="Markdown"
        )

def handle_habits_stats(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    log = db.get_daily_log(user_id, today)
    
    water = log.get('water_ml', 0) if log else 0
    steps = log.get('steps', 0) if log else 0
    sleep = log.get('sleep_hours', 0) if log else 0
    
    text = (
        "📊 **Bugungi Ko'rsatkichlar**\n\n"
        f"💧 Suv: {water}/2500 ml\n"
        f"🚶 Qadamlar: {steps}\n"
        f"😴 Uyqu: {sleep} soat\n\n"
        "**Streaklar:**\n"
        f"💧 Suv: {user.get('streak_water', 0)} kun\n"
        f"😴 Uyqu: {user.get('streak_sleep', 0)} kun\n"
        f"🧠 Kayfiyat: {user.get('streak_mood', 0)} kun\n"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
