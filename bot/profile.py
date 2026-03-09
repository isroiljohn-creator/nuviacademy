from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard, gender_keyboard, goal_keyboard, allergy_keyboard, activity_level_keyboard

import traceback

from bot.keyboards import profile_inline_keyboard
from bot.languages import get_text

def handle_profile(message, bot, user_id=None):
    """Show user profile with sub-menu"""
    try:
        if user_id is None:
            user_id = message.from_user.id
            
        user = db.get_user(user_id)
        if not user:
            bot.send_message(user_id, "Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
            return

        lang = user.get('language', 'uz')

        # Helper to escape HTML special characters
        def esc(text):
            if not text: return "-"
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Get display values
        display_name = user.get('full_name') or user.get('username') or "Foydalanuvchi"
        gender_raw = user.get('gender')
        goal_raw = user.get('goal')
        activity_raw = user.get('activity_level')
        
        display_gender = get_text(f"gender_{gender_raw}", lang)
        # Fallback if key missing (e.g. raw is None or invalid), usually not needed if robust
        if f"gender_{gender_raw}" not in ["gender_male", "gender_female"]:
             display_gender = gender_raw

        display_goal = get_text(f"goal_{goal_raw}", lang)
        display_activity = get_text(f"activity_{activity_raw}", lang)

        # Format profile text
        title = get_text("profile_title", lang)
        l_name = get_text("profile_name", lang)
        l_age = get_text("profile_age", lang)
        l_gender = get_text("profile_gender", lang)
        l_height = get_text("profile_height", lang)
        l_weight = get_text("profile_weight", lang)
        l_activity = get_text("profile_activity", lang)
        l_goal = get_text("profile_goal", lang)
        l_allergy = get_text("profile_allergies", lang)
        footer = get_text("profile_next_step", lang)
        
        allergies_val = user.get('allergies')
        if not allergies_val or str(allergies_val).lower() in ["yo'q", "—", "absent", "none"]:
            allergies_display = "YO'Q"
        else:
            allergies_display = f"BOR ({allergies_val})"
        
        # Get Subscription Status
        # Get Subscription Status
        status_key = str(user.get('plan_type') or 'free') 
        status_map = {
            'free': "Bepul",
            'basic': "YASHA PLUS",
            'premium': "YASHA PLUS",
            'vip': "VIP MENTOR",
            'pro': "VIP MENTOR"
        }
        status_display = status_map.get(status_key, "Bepul")
        
        # Determine expiry date
        # Assuming you have a way to get expiry, e.g. user.get('premium_expiry') or similar.
        # For now, if we don't have exact expiry in user object readily, we might skip date or default.
        # Let's check user object keys in db.py if needed. But for now, just Status is key request.
        # If premium, show status with star.
        
        sub_info = f"⭐️ <b>Obuna:</b> {status_display}"
        
        text = (
            f"👤 <b>{esc(display_name)}</b> [{status_display}]\n\n"
            f"📋 <b>Ma'lumotlar:</b>\n"
            f"• Yoshi: {esc(user.get('age', '-'))}\n"
            f"• Bo'yi: {esc(user.get('height', '-'))} sm\n"
            f"• Vazni: {esc(user.get('weight', '-'))} kg\n"
            f"• Jinsi: {esc(display_gender)}\n"
            f"• Faollik: {esc(display_activity)}\n"
            f"• Maqsad: {esc(display_goal)}\n"
            f"• Allergiya: {esc(allergies_display)}\n\n"
            f"{sub_info}\n"
        )
        
        bot.send_message(user_id, text, reply_markup=profile_inline_keyboard(lang=lang), parse_mode="HTML")
        
    except Exception as e:
        print(f"Profile Error: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, f"❌ Profilni yuklashda xatolik: {str(e)}")

def handle_edit_profile_command(message, bot):
    """Show inline menu for editing fields"""
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(get_text("profile_name", lang), callback_data="edit_field_full_name"),
        types.InlineKeyboardButton(get_text("profile_age", lang), callback_data="edit_field_age"),
        types.InlineKeyboardButton(get_text("profile_gender", lang), callback_data="edit_field_gender"),
        types.InlineKeyboardButton(get_text("profile_height", lang), callback_data="edit_field_height"),
        types.InlineKeyboardButton(get_text("profile_weight", lang), callback_data="edit_field_weight"),
        types.InlineKeyboardButton(get_text("profile_activity", lang), callback_data="edit_field_activity"),
        types.InlineKeyboardButton(get_text("profile_goal", lang), callback_data="edit_field_goal"),
        types.InlineKeyboardButton(get_text("profile_allergies", lang), callback_data="edit_field_allergies")
    )
    bot.send_message(message.chat.id, get_text("edit_prompt_start", lang), reply_markup=markup, parse_mode="HTML")

def handle_profile_stats(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(message.chat.id, "Foydalanuvchi topilmadi.")
        return
    # Simple stats for now
    text = (
        "📊 <b>Sog'liq Statistikasi</b>\n\n"
        f"BMI (Tana Massasi Indeksi): {calculate_bmi(user.get('weight'), user.get('height'))}\n"
        f"Suv Streaki: {user.get('streak_water', 0)} kun\n"
        f"Yasha Coin: {user.get('yasha_points', 0)}"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

def calculate_bmi(weight, height):
    try:
        if not weight or not height: return "-"
        h_m = height / 100
        bmi = weight / (h_m * h_m)
        return f"{bmi:.1f}"
    except:
        return "-"

def handle_change_goal_command(message, bot):
    bot.send_message(message.chat.id, "🎯 <b>Yangi maqsadni tanlang:</b>", reply_markup=goal_keyboard(), parse_mode="HTML")

# Keep existing handle_edit_profile_menu for callback compatibility if needed, or remove if unused.
# But handle_edit_profile_command replaces the entry point.

def register_handlers(bot):
    """Register profile related handlers"""
    
    @bot.message_handler(commands=['profile'])
    def command_profile(message):
        handle_profile(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
    def back_to_main(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "Asosiy menyu", reply_markup=main_menu_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data == "edit_profile_menu")
    def callback_edit_menu(call):
        handle_edit_profile_menu(call, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_profile")
    def callback_back_profile(call):
        # Re-render profile
        # user = db.get_user(call.from_user.id) # Not directly used here, handle_profile fetches it
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Trigger profile command logic manually or send new message
        # For now just delete and say "Profilga qaytdingiz"
        bot.answer_callback_query(call.id, "Profilga qaytdingiz")
        # Re-call handle_profile to show the main profile view
        handle_profile(call.message, bot, user_id=call.from_user.id)

    @bot.callback_query_handler(func=lambda call: call.data == "refresh_profile")
    def refresh_profile_callback(call):
        bot.answer_callback_query(call.id, "Ma'lumotlar yangilanmoqda...")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot, user_id=call.from_user.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_field_"))
    def handle_edit_callback(call):
        field = call.data.replace("edit_field_", "")
        user_id = call.from_user.id
        
        bot.answer_callback_query(call.id)
        
        # Define prompts for each field
        prompts = {
            "full_name": "Yangi ismingizni kiriting:",
            "age": "Yangi yoshingizni kiriting (raqamda):",
            "gender": "Jinsingizni tanlang:",
            "height": "Yangi bo'yingizni kiriting (sm):",
            "weight": "Yangi vazningizni kiriting (kg):",
            "goal": "Yangi maqsadingizni tanlang:",
            "allergies": "Allergiyangiz bormi? (Ha/Yo'q yoki mahsulot nomlari):"
        }
        
        prompt = prompts.get(field, "Yangi qiymatni kiriting:")
        
        # Handle fields that need keyboards
        if field == "gender":
            bot.send_message(user_id, prompt, reply_markup=gender_keyboard())
        elif field == "goal":
            bot.send_message(user_id, prompt, reply_markup=goal_keyboard())
        elif field == "activity":
            bot.send_message(user_id, "Yangi faollik darajasini tanlang:", reply_markup=activity_level_keyboard())
        elif field == "allergies":
             # For allergies, we can use text input or the simple Yes/No keyboard.
             # Given the requirement "Yangi ... kiriting", text is more flexible for editing details.
             # But let's offer the keyboard first for simplicity, or just text if they want to list details.
             # Let's stick to text for editing to allow detailed input easily.
             msg = bot.send_message(user_id, "Yangi allergiya ma'lumotlarini yozing (yoki 'Yo'q' deb yozing):")
             bot.register_next_step_handler(msg, process_edit_input, bot, field)
             return
        else:
            msg = bot.send_message(user_id, prompt)
            bot.register_next_step_handler(msg, process_edit_input, bot, field)

    # Handlers for keyboard-based edits (Gender, Goal)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
    def process_gender_edit(call):
        user_id = call.from_user.id
        new_gender = call.data.split("_")[1] # male/female
        # Map to display text if needed, or store as is. DB stores 'male'/'female' usually or localized.
        # Let's verify what DB expects. onboarding.py uses 'male'/'female'.
        # Let's map to Uzbek for display consistency if DB stores raw.
        # Actually onboarding stores raw 'male'/'female'.
        
        db.update_user_profile(user_id, gender=new_gender)
        bot.answer_callback_query(call.id, "Jins yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot, user_id=user_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("goal_"))
    def process_goal_edit(call):
        user_id = call.from_user.id
        new_goal = call.data # e.g. goal_weight_loss
        # We might want to strip 'goal_' prefix or store full string.
        # onboarding stores 'weight_loss'.
        # Let's strip 'goal_' to be consistent with onboarding.
        if new_goal.startswith("goal_"):
             new_goal = new_goal.replace("goal_", "")
             
        db.update_user_profile(user_id, goal=new_goal)
        bot.answer_callback_query(call.id, "Maqsad yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot, user_id=user_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("activity_"))
    def process_activity_edit(call):
        user_id = call.from_user.id
        new_activity = call.data.replace("activity_", "")
        
        db.update_user_profile(user_id, activity_level=new_activity)
        bot.answer_callback_query(call.id, "Faollik darajasi yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot, user_id=user_id)

def process_edit_input(message, bot, field):
    """Process text input for profile editing"""
    user_id = message.from_user.id
    value = message.text
    
    try:
        # Validation and conversion
        if field == "age":
            if not value.isdigit() or not (10 <= int(value) <= 100):
                bot.send_message(user_id, "❌ Iltimos, to'g'ri yosh kiriting (10-100).")
                return
            value = int(value)
            
        elif field == "height":
            if not value.isdigit() or not (100 <= int(value) <= 250):
                bot.send_message(user_id, "❌ Iltimos, to'g'ri bo'y kiriting (100-250 sm).")
                return
            value = int(value)
            
        elif field == "weight":
            try:
                val = float(value)
                if not (30 <= val <= 300):
                    raise ValueError
                value = val
            except ValueError:
                bot.send_message(user_id, "❌ Iltimos, to'g'ri vazn kiriting (30-300 kg).")
                return
        
        # Update DB
        kwargs = {field: value}
        db.update_user_profile(user_id, **kwargs)
        
        bot.send_message(user_id, f"{field.capitalize()} yangilandi ✅")
        handle_profile(message, bot, user_id=user_id)
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        bot.send_message(user_id, "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")

