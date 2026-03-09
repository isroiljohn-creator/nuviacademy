from telebot import types
from core.db import db
from core.ai import analyze_food_image, analyze_food_text
from bot import onboarding
from bot.premium import require_premium
from bot.languages import get_text

# States (Must be integers as per DB schema)
# States (Must be integers as per DB schema)
STATE_CALORIE_PHOTO = 200
STATE_CALORIE_TEXT = 201

def show_calorie_menu(message, bot):
    lang = db.get_user_language(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(get_text("btn_calorie_photo", lang), callback_data="calorie_mode_photo"),
        types.InlineKeyboardButton(get_text("btn_calorie_text", lang), callback_data="calorie_mode_text")
    )
    
    msg_text = get_text("calorie_title", lang)
    if not msg_text:
        msg_text = "🥦 <b>Kaloriya Tahlili</b>\n\nOvqatni rasmga oling yoki nomini yozing, sun'iy intellekt uning tarkibini aniqlab beradi."

    bot.send_message(
        message.chat.id,
        msg_text,
        reply_markup=markup,
        parse_mode="HTML"
    )

def calorie_mode_callback(call, bot):
    user_id = call.from_user.id
    mode = call.data.split('_')[2]
    
    # Check Limit
    lang = db.get_user_language(user_id)
    allowed, reason = db.check_calorie_limit(user_id)
    if not allowed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(get_text("btn_get_premium_short", lang), callback_data="premium_info"))
        
        bot.send_message(
            user_id,
            f"{get_text('calorie_limit_title', lang)}\n\n{get_text('calorie_limit_desc', lang)}",
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
def handle_calorie_mode(call, bot):
    from core.utils import parse_callback
    parts = parse_callback(call.data, prefix="calorie_mode_", min_parts=3)
    
    if not parts:
        bot.send_message(call.message.chat.id, f"⚠️ Callback Error: Parse failed ({call.data})")
        return

    try:
        mode = parts[2]
        user_id = call.from_user.id
        
        lang = db.get_user_language(user_id)
        # FREE TIER LOGIC (NO AI)
        if not db.is_premium(user_id):
             markup = types.InlineKeyboardMarkup()
             markup.add(types.InlineKeyboardButton(get_text("btn_get_plus", lang), callback_data="premium_info"))
             
             msg = f"{get_text('calorie_free_limit_title', lang)}\n"
             msg += f"{get_text('calorie_free_limit_desc', lang)}"
             
             bot.send_message(call.message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")
             bot.answer_callback_query(call.id, get_text("toast_premium_only", lang), show_alert=True)
             return

        # PREMIUM LOGIC (AI Access)
        # 1. Check DB Limit
        try:
            allowed, reason = db.check_calorie_limit(user_id)
        except Exception as e:
            print(f"DB Error in calorie check: {e}")
            bot.send_message(call.message.chat.id, f"⚠️ DB Error: {str(e)}")
            return

        if not allowed:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💎 Premium olish", callback_data="premium_info"))
            
            bot.send_message(
                user_id,
                "🚫 **Limit tugadi**\n\nKaloriya skaneri Premium paketiga kiradi. Siz bugungi bepul limitdan foydalanib bo‘ldingiz. 💚",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id)
            return

        # 2. Set State
        try:
            if mode == 'photo':
                onboarding.manager.set_state(call.from_user.id, STATE_CALORIE_PHOTO)
                bot.send_message(call.message.chat.id, get_text("prompt_calorie_photo", lang))
            elif mode == 'text':
                onboarding.manager.set_state(call.from_user.id, STATE_CALORIE_TEXT)
                bot.send_message(call.message.chat.id, get_text("prompt_calorie_text", lang))
        except Exception as e:
            print(f"State Error in calorie check: {e}")
            bot.send_message(call.message.chat.id, f"⚠️ State Error: {str(e)}")
            return
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Calorie mode error: {e}")
        bot.send_message(call.message.chat.id, f"⚠️ General Error: {str(e)}")
        bot.answer_callback_query(call.id, "Xatolik yuz berdi")

def register_handlers(bot):
    # Handlers are registered in bot/handlers.py
    pass


@require_premium
def handle_calorie_photo(message, bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    status_msg = bot.send_message(user_id, get_text("status_analyzing_photo", lang), parse_mode="HTML")
    
    try:
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            log_ai_usage(bot, user_id, "scan", 1000)
        except: pass
        
        # Log Event [NEW]
        db.log_event(user_id, "calorie_scan_photo")


        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        result = analyze_food_image(downloaded_file)
        
        if result:
            db.increment_calorie_usage(user_id)
            bot.edit_message_text(result, user_id, status_msg.message_id, parse_mode="HTML")
        else:
            send_fallback_message(bot, user_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Photo Handler Error: {e}")
        send_fallback_message(bot, user_id, status_msg.message_id)
    
    onboarding.manager.clear_user(user_id)

@require_premium
def handle_calorie_text(message, bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    status_msg = bot.send_message(user_id, get_text("status_analyzing_text", lang), parse_mode="HTML")
    
    try:
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            log_ai_usage(bot, user_id, "scan", 500)
        except: pass
        
        # Log Event [NEW]
        db.log_event(user_id, "calorie_scan_text")


        result = analyze_food_text(message.text, lang=lang, user_id=user_id)
        
        if result:
            db.increment_calorie_usage(user_id)
            bot.edit_message_text(result, user_id, status_msg.message_id, parse_mode="HTML")
        else:
            send_fallback_message(bot, user_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Text Handler Error: {e}")
        send_fallback_message(bot, user_id, status_msg.message_id)
        
    onboarding.manager.clear_user(user_id)

def send_fallback_message(bot, chat_id, message_id=None):
    from bot.languages import get_text
    from core.db import db
    
    lang = db.get_user_language(chat_id)
    text = get_text("calorie_error_ai", lang)
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown")

STATE_FRIDGE_INPUT = 300
