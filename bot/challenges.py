from telebot import types
from core.db import db

from bot.keyboards import challenges_inline_keyboard

def handle_challenges_menu(message, bot):
    markup = types.InlineKeyboardMarkup()
    from telebot.types import WebAppInfo
    import os
    markup.add(types.InlineKeyboardButton("📱 Ilovani Ochish", web_app=WebAppInfo(url=os.getenv("MINI_APP_URL"))))

    bot.send_message(
        message.chat.id,
        "🔥 <b>Barcha chellenjlar bizning ilovamizda!</b>\n\nQatnashish va sovrinlarni yutish uchun pastdagi tugmani bosing 👇",
        reply_markup=markup,
        parse_mode="HTML"
    )

def handle_weekly_challenge(message, bot):
    text = (
        "📆 <b>Haftalik Chellenj</b>\n\n"
        "Vazifa: 5 kun davomida barcha odatlarni (suv, uyqu) to'liq bajarish.\n"
        "Mukofot: +50 ball\n\n"
        "Boshlash uchun shunchaki odatlarni belgilab boring!"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

def handle_monthly_challenge(message, bot):
    text = (
        "🗓 <b>Oylik Chellenj</b>\n\n"
        "Vazifa: 30 kun davomida 100,000 qadam yurish.\n"
        "Mukofot: +200 ball va 'Yasha Walker' nishoni.\n\n"
        "Hozircha qadamlar hisobi qo'lda kiritiladi."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

def handle_friends_challenge(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    
    friends = db.get_friends_leaderboard(user_id)
    
    if not friends or len(friends) <= 1:
        text = (
            "👥 <b>Do'stlar Chellenji</b>\n\n"
            "Sizda hozircha do'stlar yo'q. 😢\n\n"
            "Do'stlaringizni taklif qiling va ular bilan bellashing!\n"
            "Har bir taklif uchun +1 coin olasiz."
        )
    else:
        text = "👥 <b>Do'stlar Reytingi</b>\n\n"
        for i, (name, points) in enumerate(friends, 1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            clean_name = name if name else "Foydalanuvchi"
            text += f"{medal} <b>{clean_name}</b> — {points} coin\n"
            
        text += "\nKim ko'p coin yig'ishini sinang! 😎"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 Do'stlarni taklif qilish", callback_data="points_referral"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

def show_leaderboard_message(message, bot):
    try:
        leaders = db.get_top_users(limit=10)
        
        if not leaders:
            bot.send_message(message.chat.id, "🏆 <b>O'zbekiston Reytingi</b>\n\nHozircha ma'lumot yo'q. Birinchi bo'ling!", parse_mode="HTML")
            return

        import html
        text = "🏆 <b>O'zbekiston Reytingi (TOP 10)</b>\n\n"
        for i, (name, points) in enumerate(leaders, 1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            raw_name = name if name else f"Foydalanuvchi {i}"
            clean_name = html.escape(str(raw_name))
            safe_points = points if points else 0
            text += f"{medal} <b>{clean_name}</b> — {safe_points} coin\n"
            
        bot.send_message(message.chat.id, text, parse_mode="HTML")
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"⚠️ Reytingni yuklashda xatolik: {str(e)}"
        bot.send_message(message.chat.id, error_msg, parse_mode="HTML")

def handle_daily_challenge(call, bot):
    # Static challenge for MVP
    text = (
        "🔥 <b>Bugungi Chellenj: 100 ta O'tirib-turish (Squats)</b>\n\n"
        "Bajarib bo'lgach, 'Bajardim' tugmasini bosing.\n"
        "Mukofot: +10 ball"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Bajardim (+10 ball)", callback_data="challenge_complete_daily"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

def complete_challenge(call, bot, points):
    user_id = call.from_user.id
    db.add_points(user_id, points)
    bot.answer_callback_query(call.id, f"🎉 Tabriklaymiz! +{points} ball")
    bot.edit_message_text(
        f"✅ <b>Chellenj bajarildi!</b>\nSizga +{points} ball berildi.\nErtaga yangi chellenj kuting!",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )

def show_leaderboard(call, bot):
    try:
        leaders = db.get_top_users(limit=10)
        
        if not leaders:
            bot.answer_callback_query(call.id, "Ma'lumot topilmadi")
            return

        import html
        text = "🏆 <b>O'zbekiston Reytingi (TOP 10)</b>\n\n"
        for i, (name, points) in enumerate(leaders, 1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            raw_name = name if name else f"User {i}"
            clean_name = html.escape(str(raw_name))
            safe_points = points if points else 0
            text += f"{medal} <b>{clean_name}</b> — {safe_points} coin\n"
            
        # Cannot edit text of a photo message, so we delete and send new
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    except Exception as e:
        print(f"Leaderboard Callback Error: {e}")
        try:
            bot.answer_callback_query(call.id, "Xatolik yuz berdi. Pastga qarang 👇")
        except: pass
        bot.send_message(call.message.chat.id, f"⚠️ **Xatolik tafsilotlari:**\n\n`{str(e)}`", parse_mode="Markdown")
