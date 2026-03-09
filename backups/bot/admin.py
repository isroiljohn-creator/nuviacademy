import os
from telebot import types
import time
from core.db import db
from core.content import content_manager
from dotenv import load_dotenv
from core.utils import safe_handler

from core.config import ADMIN_IDS
print(f"DEBUG: Loaded ADMIN_IDS: {ADMIN_IDS}")

# Globals
BROADCAST_STOP = False
BATCH_SIZE = 50

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMIN_IDS:
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("📊 Statistika"),
            types.KeyboardButton("👥 Foydalanuvchilar ro‘yxati"),
            types.KeyboardButton("📨 Umumiy xabar"),
            types.KeyboardButton("🎯 Segment xabar"),
            types.KeyboardButton("💎 Premium foydalanuvchilar"),
            types.KeyboardButton("🏷 Referallar"),
            types.KeyboardButton("💳 Obunalar"),
            types.KeyboardButton("✍️ Matnlarni tahrirlash")
        )
        bot.send_message(message.chat.id, "👨‍💼 **Admin Panel**", reply_markup=markup, parse_mode="Markdown")
        
    # Register sub handlers
    register_subscription_handlers(bot)
    register_content_handlers(bot)

    @bot.message_handler(commands=['test_ai'])
    @safe_handler(bot)
    def admin_test_ai(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "🤖 AI tekshirilmoqda...")
        
        import google.generativeai as genai
        import os
        
        report = "🤖 <b>AI Test Report:</b>\n\n"
        
        # 1. Check Key
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            report += "❌ <b>Key:</b> Missing!\n"
            bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")
            return
        
        try:
            genai.configure(api_key=key)
            report += "✅ <b>Config:</b> Success\n"
        except Exception as e:
            report += f"❌ <b>Config:</b> {e}\n"
            bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")
            return

        # 2. Test Models
        models = ['gemini-2.5-flash', 'gemini-1.5-flash']
        
        for m_name in models:
            report += f"\nTesting <b>{m_name}</b>:\n"
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content("Hello", request_options={'timeout': 10})
                if response.text:
                    report += "✅ <b>Success!</b>\n"
                else:
                    report += "⚠️ <b>Empty Response</b>\n"
            except Exception as e:
                report += f"❌ <b>Error:</b> {e}\n"
        
        bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")

    @bot.message_handler(commands=['check_limit'])
    @safe_handler(bot)
    def admin_check_limit(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "⏳ Limit tekshirilmoqda...")
        
        import google.generativeai as genai
        import os
        from core.ai import AI_USAGE_STATS
        
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            bot.edit_message_text("❌ API Key topilmadi.", message.chat.id, msg.message_id)
            return

        # 1. Live Test (Quota Check)
        status_text = ""
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            # Try a very short generation
            model.generate_content("Test", request_options={'timeout': 5})
            status_text = "✅ <b>AI Ishlayapti</b> (Limit bor)"
        except Exception as e:
            if "429" in str(e):
                status_text = "❌ <b>LIMIT TUGAGAN</b> (Quota Exceeded)"
            else:
                status_text = f"⚠️ <b>Xatolik:</b> {str(e)[:50]}..."

        # 2. Format Stats
        stats_text = (
            f"\n\n📊 <b>Ishlatilgan Limitlar (Restartdan beri):</b>\n"
            f"🏋️‍♂️ Mashqlar: {AI_USAGE_STATS['workout']}\n"
            f"🥗 Menyular: {AI_USAGE_STATS['meal']}\n"
            f"💬 Chat: {AI_USAGE_STATS['chat']}\n"
            f"👁 Vision: {AI_USAGE_STATS['vision']}\n"
            f"🛒 Shopping: {AI_USAGE_STATS['shopping']}\n"
            f"🆘 Support: {AI_USAGE_STATS['support']}\n"
            f"❌ Xatoliklar: {AI_USAGE_STATS['errors']}\n"
            f"-------------------\n"
            f"🔥 <b>Jami So'rovlar: {AI_USAGE_STATS['total_requests']}</b>"
        )
        
        full_text = status_text + stats_text
        bot.edit_message_text(full_text, message.chat.id, msg.message_id, parse_mode="HTML")

    @bot.message_handler(commands=['test_full'])
    @safe_handler(bot)
    def admin_test_full(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "🧪 To'liq test boshlandi (Fallback bilan)...")
        
        from core.ai import ask_gemini
        
        prompt = "Siz dietologsiz. 3 kunlik menu tuzing."
        
        try:
            # Use ask_gemini which has the fallback logic (2.5 -> 1.5 -> Pro)
            response_text = ask_gemini("Siz yordamchisiz.", prompt)
            
            if response_text:
                bot.edit_message_text(f"✅ **Success!**\nLength: {len(response_text)}\n\nPreview: {response_text[:100]}...", message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("⚠️ **Empty Response from ask_gemini**", message.chat.id, msg.message_id)
                
        except Exception as e:
            # This catches the "All AI models failed" exception
            bot.edit_message_text(f"❌ **Fallback Failed:** {e}", message.chat.id, msg.message_id)

    @bot.message_handler(commands=['resetdb'])
    def admin_reset_db(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        msg = bot.send_message(message.chat.id, "⚠️ **DIQQAT!**\n\nBu buyruq butun bazani o'chirib yuboradi (foydalanuvchilar, loglar, hamma narsa). \n\nDavom etish uchun 'TASDIQLAYMAN' deb yozing.", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_reset_db_confirm, bot)

    def process_reset_db_confirm(message, bot):
        if message.text == "TASDIQLAYMAN":
            try:
                db.reset_db()
                bot.send_message(message.chat.id, "✅ Baza muvaffaqiyatli tozalandi va qayta yaratildi.")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
        else:
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")

    @bot.message_handler(func=lambda message: "Statistika" in message.text and message.from_user.id in ADMIN_IDS)
    def admin_stats(message):
        try:
            stats = db.get_stats()
            
            # Safe retrieval with defaults
            total = stats.get('total', 0)
            active = stats.get('active', 0)
            premium = stats.get('premium', 0)
            gender_stats = stats.get('gender', {})
            goal_stats = stats.get('goal', {})
            
            # Translations
            # Translations
            gender_map = {
                "male": "Erkak",
                "female": "Ayol",
                None: "Ro'yxatdan o'tmagan"
            }
            goal_map = {
                "weight_loss": "Vazn tashlash 🔻",
                "muscle_gain": "Vazn olish 🔺",
                "health": "Vaznni ushlab turish ❤️",
                None: "Ro'yxatdan o'tmagan"
            }

            # Dynamic formatting for gender
            gender_text = ""
            for k, v in gender_stats.items():
                # Handle None key or string "None"
                if k == "None": k = None
                label = gender_map.get(k, k if k else "Ro'yxatdan o'tmagan")
                gender_text += f"- {label}: {v}\n"
            if not gender_text: gender_text = "Ma'lumot yo'q"

            # Dynamic formatting for goal
            goal_text = ""
            for k, v in goal_stats.items():
                if k == "None": k = None
                label = goal_map.get(k, k if k else "Ro'yxatdan o'tmagan")
                goal_text += f"- {label}: {v}\n"
            if not goal_text: goal_text = "Ma'lumot yo'q"
            
            text = (
                f"📊 <b>Statistika</b>\n\n"
                f"👥 Jami foydalanuvchilar: {total}\n"
                f"✅ Faol foydalanuvchilar: {active}\n"
                f"💎 Premium foydalanuvchilar: {premium}\n\n"
                f"👨👩 <b>Jins bo'yicha:</b>\n{gender_text}\n"
                f"🎯 <b>Maqsad bo'yicha:</b>\n{goal_text}\n"
                f"🏃 <b>Faollik:</b>\n"
                f"- Kam harakat: {stats.get('activity', {}).get('sedentary', 0)}\n"
                f"- Yengil: {stats.get('activity', {}).get('light', 0)}\n"
                f"- Faol: {stats.get('activity', {}).get('active', 0)}\n"
                f"- Atlet: {stats.get('activity', {}).get('athlete', 0)}\n\n"
                f"🔗 <b>Manbalar (UTM):</b>\n"
            )
            
            # UTM Stats logic (quick aggregation)
            # This should ideally be in db.get_stats(), but for MVP I'll fetch here or update db.py
            # Let's update db.py to include 'utm' in get_stats() 
            # OR just do it dynamically here if we trust get_stats returns raw dict.
            # Assuming db.get_stats() needs update.
            # Let's verify what db.get_stats() returns.
            
            utm_stats = stats.get('utm', {})
            for k, v in utm_stats.items():
                if k == "None": k = "Organic/Unknown"
                text += f"- {k}: {v}\n"
                
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            
        except Exception as e:
            print(f"ERROR in admin_stats: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")

    @bot.message_handler(func=lambda message: "Foydalanuvchilar ro‘yxati" in message.text)
    def admin_user_list(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        show_user_list_page(message.chat.id, 1, bot)

    def show_user_list_page(chat_id, page, bot, message_id=None):
        try:
            PAGE_SIZE = 20
            users, total_count = db.get_users_paginated(page, PAGE_SIZE)
            
            if not users:
                text = "👥 Foydalanuvchilar topilmadi."
                if message_id:
                    bot.edit_message_text(text, chat_id, message_id)
                else:
                    bot.send_message(chat_id, text)
                return

            total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
            
            text = f"👥 <b>Foydalanuvchilar (Jami: {total_count})</b>\nSahifa: {page}/{total_pages}\n\n"
            
            for user in users:
                uid = user['telegram_id']
                name = user['full_name']
                username = user['username']
                phone = user['phone'] or "N/A"
                goal = user['goal'] or "N/A"
                
                # Goal Translation
                goal_map = {
                    "weight_loss": "Vazn tashlash 🔻",
                    "muscle_gain": "Vazn olish 🔺",
                    "health": "Vazn saqlash ❤️",  # Shortened for list view
                    "None": "-",
                    None: "-"
                }
                
                # Clean up data
                if goal == "N/A": goal = "-"
                formatted_goal = goal_map.get(goal, goal)

                # Check premium
                is_prem = ""
                if user.get('premium_until'):
                    from datetime import datetime
                    if user['premium_until'] > datetime.now():
                        is_prem = "💎"
                
                display_name = f"@{username}" if username else (name if name else "Noma'lum")
                
                import html
                safe_name = html.escape(str(display_name))
                
                # Simplified format without excessive | and ID icon clutter if preferred, but user liked ID.
                # Just tidying up the English terms.
                text += f"🆔 <code>{uid}</code> | {safe_name} | {formatted_goal} {is_prem}\n"
            
            # Pagination Buttons
            markup = types.InlineKeyboardMarkup()
            row = []
            if page > 1:
                row.append(types.InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_users_page_{page-1}"))
            if page < total_pages:
                row.append(types.InlineKeyboardButton("Keyingi ➡️", callback_data=f"admin_users_page_{page+1}"))
            
            if row:
                markup.row(*row)
            
            if message_id:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
                
        except Exception as e:
            print(f"Error in user list: {e}")
            if message_id:
                bot.send_message(chat_id, f"❌ Xatolik: {e}")
            else:
                bot.send_message(chat_id, f"❌ Xatolik: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_users_page_"))
    def handle_user_pagination(call):
        if call.from_user.id not in ADMIN_IDS:
            return
        
        from core.utils import parse_callback
        parts = parse_callback(call.data, prefix="admin_users_page_", min_parts=4)
        
        if not parts:
            bot.answer_callback_query(call.id, "Xatolik")
            return

        try:
            page = int(parts[3])
            show_user_list_page(call.message.chat.id, page, bot, call.message.message_id)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Pagination error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    @bot.message_handler(func=lambda message: "Premium foydalanuvchilar" in message.text)
    def admin_premium_list(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        # This is a bit expensive without a direct DB query, but fine for MVP
        users = db.get_users_by_segment(is_premium=True)
        
        text = f"💎 <b>Premium Foydalanuvchilar:</b>\n\n"
        for uid, name, username in users[:20]:
            # Prioritize username, then name, then fallback
            display_name = f"@{username}" if username else (name if name else "Noma'lum")
            
            # Escape HTML in name
            import html
            safe_name = html.escape(display_name)
            
            text += f"🆔 <code>{uid}</code> | {safe_name}\n"
            
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    @bot.message_handler(func=lambda message: "Referallar" in message.text)
    def admin_referrals(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        top_referrers = db.get_top_referrals(10)
        
        text = "🏷 <b>TOP 10 Referallar:</b>\n\n"
        for item in top_referrers:
            import html
            safe_name = html.escape(item['name']) if item['name'] else "Noma'lum"
            text += f"👤 {safe_name} (ID: <code>{item['id']}</code>) — {item['count']} ta taklif\n"
            
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    @bot.message_handler(func=lambda message: "Umumiy xabar" in message.text)
    def admin_broadcast_start(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        print(f"DEBUG: Admin broadcast started by {message.from_user.id}")
        try:
            msg = bot.send_message(message.chat.id, "Xabarni yuboring (matn, rasm, video, ovozli xabar):", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_broadcast, bot, "all")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda message: "Segment xabar" in message.text)
    def admin_segment_start(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        markup = types.InlineKeyboardMarkup()
        # Gender
        markup.row(
            types.InlineKeyboardButton("👨 Erkaklar", callback_data="seg_gender_male"),
            types.InlineKeyboardButton("👩 Ayollar", callback_data="seg_gender_female")
        )
        # Plan Status
        markup.row(
            types.InlineKeyboardButton("💎 Premium", callback_data="seg_premium_True"),
            types.InlineKeyboardButton("👤 Bepul", callback_data="seg_premium_False")
        )
        # Goals
        markup.add(types.InlineKeyboardButton("🔻 Vazn tashlash", callback_data="seg_goal_weight_loss"))
        markup.add(types.InlineKeyboardButton("🔺 Vazn olish", callback_data="seg_goal_muscle_gain"))
        markup.add(types.InlineKeyboardButton("❤️ Vaznni ushlab turish", callback_data="seg_goal_health"))
        
        # Activity
        markup.row(
            types.InlineKeyboardButton("🪑 Kam harakat", callback_data="seg_activity_sedentary"),
            types.InlineKeyboardButton("🏃 O'rtacha", callback_data="seg_activity_moderate")
        )
        markup.add(types.InlineKeyboardButton("🔥 Faol / Atlet", callback_data="seg_activity_athlete"))
        
        bot.send_message(message.chat.id, "Segmentni tanlang:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.reply_to_message and message.from_user.id in ADMIN_IDS)
    def admin_reply_to_user(message):
        """Handle admin replying to a user's feedback"""
        try:
            original_text = message.reply_to_message.text or message.reply_to_message.caption
            if not original_text:
                return
            
            # Extract User ID from the original message text
            # Format expected: "👤 Foydalanuvchi: Name (ID: 12345)"
            import re
            match = re.search(r"\(ID: (\d+)\)", original_text)
            
            if match:
                user_id = int(match.group(1))
                reply_text = message.text or "Rasm/Video"
                
                # Send to user
                try:
                    bot.copy_message(user_id, message.chat.id, message.message_id)
                    bot.reply_to(message, f"✅ Xabar foydalanuvchiga (ID: {user_id}) yuborildi.")
                except Exception as e:
                    bot.reply_to(message, f"❌ Yuborishda xatolik: {e}")
            else:
                bot.reply_to(message, "⚠️ Foydalanuvchi ID si topilmadi. Xabar formatini tekshiring.")
                
        except Exception as e:
            print(f"Error in admin reply: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("seg_"))
    def admin_segment_select(call):
        if call.from_user.id not in ADMIN_IDS:
            return
            
        segment = call.data.split("_")[1:] # ['gender', 'Erkak'] or ['premium', 'True']
        msg = bot.send_message(call.message.chat.id, f"Tanlangan segment: {segment[0]}={segment[1]}. Xabarni yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_broadcast, bot, segment)

import threading

def process_broadcast(message, bot, segment):
    # Wrapper to run broadcast in background
    thread = threading.Thread(target=_broadcast_worker, args=(message, bot, segment))
    thread.daemon = True # Daemonize to not block shutdown if stuck
    thread.start()
    bot.send_message(message.chat.id, "🚀 Xabar yuborish fonda boshlandi. Menyu orqali ishlatishda davom etishingiz mumkin.")

def _broadcast_worker(message, bot, segment):
    """
    Worker function running in a separate thread.
    """
    try:
        # Check if user cancelled
        if message.text and message.text.startswith("/"):
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")
            return

        users = []
        if segment == "all":
            users = db.get_active_users()
        else:
            key, value = segment[0], segment[1]
            if key == "gender":
                users = db.get_users_by_segment(gender=value)
            elif key == "goal":
                users = db.get_users_by_segment(goal=value)
            elif key == "premium":
                is_prem = (value == "True")
                users = db.get_users_by_segment(is_premium=is_prem)
            elif key == "activity":
                users = db.get_users_by_segment(activity_level=value)
        
        if not users:
            bot.send_message(message.chat.id, "❌ Foydalanuvchilar topilmadi.")
            return

        msg = bot.send_message(message.chat.id, "⏳ Yuborish boshlanmoqda...")
        status_msg_id = msg.message_id
        
        success = 0
        failed = 0
        offset = 0
        start_time = time.time()
        
        photo = None
        if message.content_type == 'photo':
            photo = message.photo[-1].file_id

        # Use batch processing
        target_segment = segment # 'all' or list

        while True:
            if BROADCAST_STOP:
                bot.send_message(message.chat.id, "🛑 Yuborish to'xtatildi!")
                return

            # Fetch batch
            users_batch_data = []
            if target_segment == "all":
                users_batch_data = db.get_active_users_batch(offset=offset, limit=BATCH_SIZE)
            else:
                key, value = target_segment[0], target_segment[1]
                if key == "gender":
                    users_batch_data = db.get_users_by_segment_batch(gender=value, offset=offset, limit=BATCH_SIZE)
                elif key == "goal":
                    users_batch_data = db.get_users_by_segment_batch(goal=value, offset=offset, limit=BATCH_SIZE)
                elif key == "premium":
                    is_prem = (value == "True")
                    users_batch_data = db.get_users_by_segment_batch(is_premium=is_prem, offset=offset, limit=BATCH_SIZE)
                elif key == "activity":
                    users_batch_data = db.get_users_by_segment_batch(activity_level=value, offset=offset, limit=BATCH_SIZE)

            if not users_batch_data:
                break # No more users in this segment or overall
            
            # Process batch
            for user_id in users_batch_data:
                if BROADCAST_STOP:
                    break
                    
                try:
                    if photo:
                        bot.send_photo(user_id, photo, caption=message.caption)
                    else:
                        bot.send_message(user_id, message.text)
                    success += 1
                except Exception as e:
                    # If blocked, mark inactive
                    if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                        db.set_user_active(user_id, False)
                    failed += 1
                    # print(f"Failed to send to {user_id}: {e}")
                
            # Update status every batch
            elapsed = int(time.time() - start_time)
            try:
                bot.edit_message_text(f"⏳ Yuborilmoqda...\n✅: {success}\n❌: {failed}\n⏱: {elapsed}s", message.chat.id, status_msg_id)
            except: pass
            
            offset += BATCH_SIZE
            time.sleep(1) # Sleep between batches to be nice to API limits
            
        bot.send_message(message.chat.id, f"🏁 Tugadi!\n✅ Muvaffaqiyatli: {success}\n❌ Yetib bormadi: {failed}")
        
    except Exception as e:
        print(f"Error in process_broadcast: {e}")
        try:
            bot.send_message(message.chat.id, f"❌ Xabar yuborishda xatolik: {e}")
        except:
            pass



# === Subscription Management ===

def register_subscription_handlers(bot):
    @bot.message_handler(func=lambda message: "Obunalar" in message.text and message.from_user.id in ADMIN_IDS)
    def admin_subs_start(message):
        msg = bot.send_message(message.chat.id, "Foydalanuvchi ID raqamini yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_subs_user_id, bot)

    def process_subs_user_id(message, bot):
        try:
            if not message.text.isdigit():
                bot.send_message(message.chat.id, "❌ ID raqam bo'lishi kerak.")
                return
            
            target_id = int(message.text)
            user = db.get_user(target_id)
            
            if not user:
                bot.send_message(message.chat.id, f"❌ Foydalanuvchi topilmadi: {target_id}")
                return
            
            is_prem = db.is_premium(target_id)
            status = "✅ Premium" if is_prem else "❌ Oddiy"
            until = user.get('premium_until', 'Yo‘q')
            
            text = (
                f"👤 **Foydalanuvchi:** {user.get('full_name', 'Noma’lum')}\n"
                f"🆔 ID: `{target_id}`\n"
                f"💎 Status: {status}\n"
                f"📅 Tugash: {until}\n\n"
                "Amalni tanlang:"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("➕ Obuna qo'shish", callback_data=f"sub_add_{target_id}"))
            markup.add(types.InlineKeyboardButton("➖ Obunani o'chirish", callback_data=f"sub_remove_{target_id}"))
            markup.add(types.InlineKeyboardButton("🔄 Limitni tiklash (0)", callback_data=f"sub_reset_{target_id}"))
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sub_add_") or call.data.startswith("sub_remove_") or call.data.startswith("sub_reset_"))
    def handle_sub_action(call):
        if call.from_user.id not in ADMIN_IDS:
            return
            
        action, target_id = call.data.split("_")[1], int(call.data.split("_")[2])
        
        if action == "reset":
            db.reset_user_ai_limits(target_id)
            bot.answer_callback_query(call.id, "✅ Limitlar 0 ga tushirildi!")
            return
        
        if action == "remove":
            db.remove_premium(target_id)
            bot.edit_message_text(
                f"✅ Foydalanuvchi ({target_id}) dan Premium olib tashlandi.",
                call.message.chat.id,
                call.message.message_id
            )
            try:
                bot.send_message(target_id, "❌ Sizning Premium obunangiz admin tomonidan bekor qilindi.")
            except:
                pass
                
        elif action == "add":
            # Choose Plan Type
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⭐️ Premium", callback_data=f"sub_plan_premium_{target_id}"))
            markup.add(types.InlineKeyboardButton("👑 VIP", callback_data=f"sub_plan_vip_{target_id}"))
            
            bot.edit_message_text(
                "Qaysi tarifni bermoqchisiz?",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        # STOP LOADING SPINNER
        try:
            bot.answer_callback_query(call.id)
        except: pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sub_plan_"))
    def handle_sub_plan_selection(call):
        # 1. STOP SPINNER IMMEDIATELY
        try:
            bot.answer_callback_query(call.id)
        except: pass
        
        # 2. Check Auth
        if call.from_user.id not in ADMIN_IDS: 
            print(f"DEBUG: Unauthorized access attempt to sub_plan by {call.from_user.id}")
            return
        
        try:
            parts = call.data.split("_")
            plan_type = parts[2] # premium or vip
            target_id = int(parts[3])
            
            msg = bot.send_message(call.message.chat.id, f"<b>{plan_type.upper()}</b> tarifi uchun necha kun qo'shmoqchisiz? (masalan: 30)", parse_mode="HTML", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_subs_days, bot, target_id, plan_type)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Xatolik: {e}")
            print(f"Sub Plan Select Error: {e}")

    def process_subs_days(message, bot, target_id, plan_type):
        try:
            if not message.text.isdigit():
                bot.send_message(message.chat.id, "❌ Son kiritishingiz kerak.")
                return

            days = int(message.text)
            # Use new tiered setter
            db.set_user_plan(target_id, plan_type, days)
            
            bot.send_message(message.chat.id, f"✅ Foydalanuvchi ({target_id}) ga {days} kun <b>{plan_type.upper()}</b> tarifi qo'shildi.", parse_mode="HTML")
            
            try:
                bot.send_message(target_id, f"🎉 Tabriklaymiz! Admin sizga {days} kunlik **{plan_type.upper()}** obuna sovg'a qildi!", parse_mode="Markdown")
            except:
                pass
                
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {e}")
            print(f"Sub Add Error: {e}")

    @bot.message_handler(commands=['clear_workouts'])
    def admin_clear_workouts_start(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(
            message.chat.id, 
            "⚠️ <b>DIQQAT!</b>\n\nBu buyruq BARCHA foydalanuvchilarning eski AI mashq rejalarini o'chirib yuboradi.\nUlarga yangi mashqlar kerak bo'lganda qaytadan generatsiya qilishadi.\n\nDavom etish uchun <code>TASDIQLAYMAN</code> deb yozing:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_clear_workouts_confirmation, bot)

    def process_clear_workouts_confirmation(message, bot):
        if message.text == "TASDIQLAYMAN":
            count = db.clear_all_workout_caches()
            bot.send_message(message.chat.id, f"✅ Bajarildi! {count} ta eski mashq rejasi o'chirib yuborildi.")
        else:
            bot.send_message(message.chat.id, "❌ Bekor qilindi. Tasdiqlash kodi noto'g'ri.")

    @bot.message_handler(commands=['gift_all'])
    def admin_gift_all_start(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        # Parse args
        # /gift_all 5
        parts = message.text.split()
        days = 7
        if len(parts) > 1 and parts[1].isdigit():
            days = int(parts[1])
            
        msg = bot.send_message(
            message.chat.id, 
            f"⚠️ **DIQQAT! KATTA OPERATSIYA**\n\nSiz **BARCHA** foydalanuvchilarga {days} kunlik Premium (Trial) bermoqchisiz.\n\nTasdiqlash uchun **TASDIQLAYMAN** deb yozing.",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_gift_all_confirm, bot, days)

    def process_gift_all_confirm(message, bot, days):
        if message.text == "TASDIQLAYMAN":
            status = bot.send_message(message.chat.id, "⏳ Bajarilmoqda... Bu biroz vaqt olishi mumkin.")
            try:
                count = db.gift_premium_to_all(days=days, plan_type="trial")
                bot.edit_message_text(f"✅ Muvaffaqiyatli! {count} ta foydalanuvchiga {days} kunlik Premium berildi.", message.chat.id, status.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, status.message_id)
        else:
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")

def register_content_handlers(bot):
    @bot.message_handler(func=lambda message: "Matnlarni tahrirlash" in message.text and message.from_user.id in ADMIN_IDS)
    def admin_content_start(message):
        # List categories or show keys
        # For simplicity, let's show keys directly or search
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # We can group by category if we had many, but for now list all or search
        markup.add(types.InlineKeyboardButton("🔍 Qidirish", callback_data="content_search"))
        
        # Add some common keys manually or fetch top ones
        all_content = content_manager.get_all()
        for key in list(all_content.keys())[:5]:
            markup.add(types.InlineKeyboardButton(f"📝 {key}", callback_data=f"content_edit_{key}"))
            
        bot.send_message(message.chat.id, "Matnlarni boshqarish. Qidiruvdan foydalaning yoki ro'yxatdan tanlang:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "content_search")
    def admin_content_search_prompt(call):
        if call.from_user.id not in ADMIN_IDS: return
        msg = bot.send_message(call.message.chat.id, "Kalit so'zni kiriting (masalan: welcome):", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_content_search, bot)

    def process_content_search(message, bot):
        query = message.text.lower()
        all_content = content_manager.get_all()
        matches = [k for k in all_content.keys() if query in k.lower()]
        
        if not matches:
            bot.send_message(message.chat.id, "❌ Hech narsa topilmadi.")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key in matches[:10]: # Limit to 10
            markup.add(types.InlineKeyboardButton(f"📝 {key}", callback_data=f"content_edit_{key}"))
            
        bot.send_message(message.chat.id, f"🔍 '{query}' bo'yicha natijalar:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("content_edit_"))
    def admin_content_edit_prompt(call):
        if call.from_user.id not in ADMIN_IDS: return
        key = call.data.replace("content_edit_", "")
        current_val = content_manager.get(key)
        
        text = f"🔑 **Kalit:** `{key}`\n\n📄 **Hozirgi matn:**\n{current_val}\n\n✏️ Yangi matnni yuboring:"
        msg = bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_content_update, bot, key)

    def process_content_update(message, bot, key):
        new_val = message.text
        if new_val.startswith("/"):
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")
            return
            
        else:
            try:
                content_manager.set(key, new_val)
                bot.send_message(message.chat.id, f"✅ '{key}' muvaffaqiyatli yangilandi!")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Saqlashda xatolik: {e}")

    @bot.message_handler(commands=['seed'])
    def admin_seed_content(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        defaults = {
            "premium_title": "💎 **Premium Bo'limi**",
            "premium_desc": "Premium imkoniyatlari:\n• Cheksiz AI maslahatlari\n• Foto orqali kaloriya aniqlash\n• Chellenjlarda 2x ball",
            "welcome_message": "Assalomu alaykum! YASHA Fitness Botiga xush kelibsiz.",
            "onboarding_name": "Ismingizni kiriting:",
            "onboarding_age": "Yoshingizni kiriting (faqat raqam):"
        }
        
        count = 0
        for key, value in defaults.items():
            if not content_manager.get(key):
                content_manager.set(key, value)
                count += 1
        
        bot.send_message(message.chat.id, f"✅ {count} ta yangi matn bazaga qo'shildi.")


