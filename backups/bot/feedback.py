import os
from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard
from dotenv import load_dotenv

load_dotenv()
MAIN_ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
ADMIN_IDS = [MAIN_ADMIN_ID, 1392501306]

def handle_feedback_start(message, bot):
    user_id = message.from_user.id
    with open("assets/qayta_aloqa.png", "rb") as photo:
        msg = bot.send_photo(user_id, photo, caption="Fikringizni yozing:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_feedback, bot)

def process_feedback(message, bot):
    user_id = message.from_user.id
    text = message.text
    
    # If user cancels or sends a command
    if text.startswith("/"):
        bot.send_message(user_id, "Bekor qilindi.", reply_markup=main_menu_keyboard())
        return

    # Save to DB
    db.add_feedback(user_id, text)
    
    # Notify User
    bot.send_message(user_id, "✅ Rahmat! Fikringiz qabul qilindi va jamoamizga yuborildi.", reply_markup=main_menu_keyboard())
    
    # Forward to Admins
    print(f"DEBUG: Attempting to forward feedback to ADMIN_IDS: {ADMIN_IDS}")
    user = db.get_user(user_id)
    user_name = user.get('full_name') or user.get('username') or "Unknown"
    
    import html
    safe_name = html.escape(str(user_name))
    safe_text = html.escape(str(text))
    
    admin_msg = (
        f"🆕 <b>Yangi feedback keldi!</b>\n"
        f"👤 Foydalanuvchi: {safe_name} (ID: {user_id})\n"
        f"📝 Matn:\n{safe_text}"
    )
    
    for admin_id in ADMIN_IDS:
        if admin_id:
            try:
                bot.send_message(admin_id, admin_msg, parse_mode="HTML")
                print(f"DEBUG: Feedback forwarded to {admin_id}.")
            except Exception as e:
                print(f"Failed to forward feedback to admin {admin_id}: {e}")

def register_handlers(bot):
    pass # Implicitly handled via menu

