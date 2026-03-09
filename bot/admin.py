import os
from telebot import types
import time
from bot.languages import get_text
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
    from bot.keyboards import admin_developer_keyboard, admin_analytics_keyboard

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMIN_IDS:
            return

        # WebApp URL Construction
        import os
        base_url = os.getenv("MINI_APP_URL", "https://yasha-insights.up.railway.app")
        if base_url.endswith("/"): base_url = base_url[:-1]
        webapp_url = f"{base_url}/admin-insights/"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        # 1. Top - Mini App Dashboard (Prominent)
        markup.add(
            types.KeyboardButton("👨‍💻 DASTURCHI")
        )
        
        # 2. Main Controls
        markup.add(
            types.KeyboardButton("📊 Statistika"),
            types.KeyboardButton("👥 Foydalanuvchilar")
        )
        markup.add(
            types.KeyboardButton("📤 Xabar yuborish"),
            types.KeyboardButton("💳 Obunalar")
        )
        bot.send_message(message.chat.id, "👨‍💼 **Admin Panel**", reply_markup=markup, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: message.text == "👨‍💻 DASTURCHI" and message.from_user.id in ADMIN_IDS)
    def developer_menu_handler(message):
        from bot.keyboards import admin_developer_keyboard
        bot.send_message(message.chat.id, "👨‍💻 **Dasturchi Paneli**\n\nBuyruqni tanlang:", reply_markup=admin_developer_keyboard(), parse_mode="Markdown")
        
    # Register sub handlers
    register_subscription_handlers(bot)

    
    @bot.message_handler(commands=['dashboard'])
    def dashboard_command(message):
        if message.from_user.id not in ADMIN_IDS: return
        import os
        base_url = os.getenv("MINI_APP_URL", "https://yasha-insights.up.railway.app")
        if base_url.endswith("/"): base_url = base_url[:-1]
        webapp_url = f"{base_url}/admin-insights/"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚦 Open Dashboard (Inline)", web_app=types.WebAppInfo(url=webapp_url)))
        
        bot.send_message(message.chat.id, "👇 **Dashboardga kirish (Muqobil yo'l)**", reply_markup=markup, parse_mode="Markdown")

    @bot.message_handler(commands=['analytics_pro'])
    def analytics_pro_command(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        text = (
            "🚀 **YASHA Advanced Analytics**\n\n"
            "Bo'limni tanlang:\n"
            "• **Growth**: Userlar ko'payishi\n"
            "• **Funnel**: Konversiya yo'li\n"
            "• **Retention**: Foydalanuvchi qaytishi\n"
            "• **Premium**: Moliyaviy ko'rsatkichlar"
        )
        bot.send_message(message.chat.id, text, reply_markup=admin_analytics_keyboard(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_stats_'))
    def analytics_callback_handler(call):
        if call.from_user.id not in ADMIN_IDS: return
        
        action = call.data.replace('admin_stats_', '')
        from core.analytics import get_growth_stats, get_funnel_stats, get_retention_stats, get_premium_stats
        from bot.admin import generate_analytics_report
        
        bot.answer_callback_query(call.id, "Yuklanmoqda...")
        
        try:
            if action == 'growth':
                report, chart = get_growth_stats()
                bot.send_photo(call.message.chat.id, chart, caption=report, parse_mode="Markdown")
            elif action == 'funnel':
                report, chart = get_funnel_stats()
                bot.send_photo(call.message.chat.id, chart, caption=report, parse_mode="Markdown")
            elif action == 'retention':
                report, chart = get_retention_stats()
                bot.send_photo(call.message.chat.id, chart, caption=report, parse_mode="Markdown")
            elif action == 'premium':
                report, chart = get_premium_stats()
                bot.send_photo(call.message.chat.id, chart, caption=report, parse_mode="Markdown")
            elif action == 'report':
                report = generate_analytics_report()
                bot.send_message(call.message.chat.id, report, parse_mode="HTML")
            elif action == 'menu_rollout':
                report = generate_menu_rollout_report()
                bot.send_message(call.message.chat.id, report, parse_mode="HTML")
            elif action == 'workout_rollout':
                report = generate_workout_rollout_report()
                bot.send_message(call.message.chat.id, report, parse_mode="HTML")
            elif action == 'refresh':
                bot.delete_message(call.message.chat.id, call.message.message_id)
                analytics_pro_command(call.message)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Xatolik: {e}")




    @bot.message_handler(commands=['test_ai'])

    @safe_handler(bot)
    def admin_test_ai(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "🤖 AI tekshirilmoqda...")
        
        from google import genai
        import os
        
        report = "🤖 <b>AI Test Report (New SDK):</b>\n\n"
        
        # 1. Check Key
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            report += "❌ <b>Key:</b> Missing!\n"
            bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")
            return
        
        try:
            client = genai.Client(api_key=key)
            report += "✅ <b>Client Init:</b> Success\n"
        except Exception as e:
            report += f"❌ <b>Client Init:</b> {e}\n"
            bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")
            return

        # 2. Test Models
        models = ['gemini-2.0-flash', 'gemini-1.5-flash']
        
        for m_name in models:
            report += f"\nTesting <b>{m_name}</b>:\n"
            try:
                response = client.models.generate_content(
                    model=m_name,
                    contents="Hello"
                )
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
        
        from google import genai
        import os
        from core.ai import AI_USAGE_STATS
        
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            bot.edit_message_text("❌ API Key topilmadi.", message.chat.id, msg.message_id)
            return

        # 1. Live Test (Quota Check)
        status_text = ""
        try:
            client = genai.Client(api_key=key)
            # Try a very short generation
            client.models.generate_content(
                model='gemini-2.0-flash',
                contents="Test"
            )
            status_text = "✅ <b>AI Ishlayapti</b> (Limit bor)"
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
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

    @bot.message_handler(commands=['sync_videos_now'])
    @safe_handler(bot)
    def admin_sync_videos_command(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "🔄 Sync ishga tushirildi... (Fondagi jarayon)")
        
        try:
            from core.maintenance import start_sync_thread
            start_sync_thread(bot, message.chat.id)
        except Exception as e:
            bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, msg.message_id)

    @bot.message_handler(commands=['populate_exercises'])
    @safe_handler(bot)
    def admin_populate_exercises(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        bot.send_message(message.chat.id, "🔄 YMove'dan mashqlar yuklanmoqda...")
        
        try:
            from core.ymove import _fetch_all_exercises
            exercises = _fetch_all_exercises()
            
            if not exercises:
                bot.send_message(message.chat.id, "❌ Mashqlar topilmadi!")
                return
            
            bot.send_message(message.chat.id, f"📥 {len(exercises)} ta mashq topildi. Bazaga saqlanmoqda...")
            count = 0
            for ex in exercises:
                try:
                    cat = (ex.get('category', '') or '').lower()
                    if 'upper' in cat or 'chest' in cat or 'shoulder' in cat: category = 'Upper Body'
                    elif 'lower' in cat or 'leg' in cat: category = 'Lower Body'
                    elif 'cardio' in cat: category = 'Cardio'
                    elif 'full' in cat: category = 'Full Body'
                    else: category = 'Upper Body'
                    
                    db.save_exercise(
                        name=ex['title'],
                        video_url=ex.get('videoUrl'),
                        category=category,
                        difficulty=(ex.get('difficulty', 'beginner') or 'beginner').lower(),
                        description=ex.get('description'),
                        muscle_group=ex.get('primaryMuscle'),
                        equipment=ex.get('equipment'),
                        duration_sec=ex.get('duration', 60)
                    )
                    count += 1
                    if count % 50 == 0:
                        bot.send_message(message.chat.id, f"📊 {count} ta saqlandi...")
                except Exception as e:
                    print(f"Error saving exercise: {e}")
            
            bot.send_message(message.chat.id, f"✅ {count} ta mashq saqlandi!")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

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
            vip = stats.get('vip', 0)
            trial = stats.get('trial', 0)
            incomplete = stats.get('incomplete', 0)
            
            gender_stats = stats.get('gender', {})
            goal_stats = stats.get('goal', {})
            
            # Translations
            gender_map = {
                "male": "Erkak",
                "female": "Ayol",
                None: "Ro'yxatdan o'tmagan"
            }
            goal_map = {
                "lose_weight": "Vazn tashlash 🔻",
                "gain_muscle": "Vazn olish 🔺",
                "maintain": "Vaznni ushlab turish ❤️",
                "health": "Sog'lom bo'lish 🌿",
                None: "Ro'yxatdan o'tmagan"
            }

            # Dynamic formatting for gender
            gender_text = ""
            for k, v in gender_stats.items():
                label = gender_map.get(k, k if k else "Ro'yxatdan o'tmagan")
                gender_text += f"- {label}: {v}\n"
            if not gender_text: gender_text = "Ma'lumot yo'q"

            # Dynamic formatting for goal
            goal_text = ""
            for k, v in goal_stats.items():
                label = goal_map.get(k, k if k else "Ro'yxatdan o'tmagan")
                goal_text += f"- {label}: {v}\n"
            if not goal_text: goal_text = "Ma'lumot yo'q"
            
            text = (
                f"📊 <b>Statistika</b>\n\n"
                f"👥 Jami foydalanuvchilar: {total}\n"
                f"✅ Faol foydalanuvchilar: {active}\n"
                f"⏸ Ro'yxatdan o'tmagan: {incomplete}\n"
                f"-------------------\n"
                f"💎 Premium: {premium}\n"
                f"👑 VIP: {vip}\n"
                f"🎁 Trial: {trial}\n"
                f"-------------------\n\n"
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
            import traceback
            print(f"ERROR in admin_stats: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")

    @bot.message_handler(commands=['analytics_feedback'])
    @safe_handler(bot)
    def admin_feedback_analytics_cmd(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        from bot.feedback import get_feedback_analytics
        try:
             report = get_feedback_analytics()
             bot.send_message(message.chat.id, report, parse_mode="HTML")
        except Exception as e:
             bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(commands=['analytics_adaptation'])
    @safe_handler(bot)
    def admin_adaptation_analytics_cmd(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        try:
            from core.adaptation import get_adaptation_analytics
            report = get_adaptation_analytics()
            bot.send_message(message.chat.id, report, parse_mode="HTML")
        except Exception as e:
             bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
            
        except Exception as e:
             bot.send_message(message.chat.id, f"❌ Xatolik: {e}")


    # --- CALLBACK BRIDGES FOR DEV MENU ---
    
    @bot.callback_query_handler(func=lambda call: call.data == "admin_analytics_btn")
    def admin_analytics_callback(call):
        try:
            if call.from_user.id in ADMIN_IDS:
                 bot.answer_callback_query(call.id)
                 
                 # Show technical analytics (different from Statistika)
                 stats = db.get_stats()
                 import datetime
                 
                 text = (
                     "📊 <b>Technical Analytics</b>\n\n"
                     f"🤖 Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                     f"👥 Total: {stats.get('total', 0)}\n"
                     f"✅ Active: {stats.get('active', 0)}\n"
                     f"💎 Premium: {stats.get('premium', 0)}\n\n"
                     "<b>Top UTM Sources:</b>\n"
                 )
                 
                 utm_stats = stats.get('utm', {})
                 for k, v in list(utm_stats.items())[:5]:
                     source = k if k else "Organic"
                     text += f"- {source}: {v}\n"
                 
                 bot.send_message(call.message.chat.id, text, parse_mode="HTML")
            else:
                 bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
        except Exception as e:
            print(f"Callback Error analytics: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "Xatolik")

    @bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_btn")
    def admin_broadcast_callback(call):
        try:
            if call.from_user.id in ADMIN_IDS:
                 bot.answer_callback_query(call.id)
                 # Create a pseudo-message object for admin_broadcast_start
                 class PseudoMessage:
                     def __init__(self, chat_id, from_user):
                         self.chat = type('obj', (object,), {'id': chat_id})
                         self.from_user = from_user
                 
                 pseudo_msg = PseudoMessage(call.message.chat.id, call.from_user)
                 admin_broadcast_start(pseudo_msg)
            else:
                 bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
        except Exception as e:
            print(f"Callback Error broadcast: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "Xatolik")
             
    
    # AI Database Cleanup Handler
    @bot.message_handler(func=lambda message: "AI Bazani Tozalash" in message.text)
    def admin_clear_ai_data(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        # Show cleanup options
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🗑 Barcha menyularni o'chirish", callback_data="clear_all_meals"),
            types.InlineKeyboardButton("👤 ID bo'yicha tozalash", callback_data="clear_user_meals")
        )
        markup.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_clear_ai"))
        
        text = (
            "🗑 <b>AI Menyu Bazasini Tozalash</b>\n\n"
            "Variantni tanlang:"
        )
        
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    
    @bot.callback_query_handler(func=lambda call: call.data == "clear_all_meals")
    def confirm_clear_all_meals(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        bot.answer_callback_query(call.id)
        
        # Confirmation for all meals
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Ha, tozala", callback_data="confirm_clear_ai"),
            types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_clear_ai")
        )
        
        text = (
            "🗑 <b>Barcha Menyularni O'chirish</b>\n\n"
            "⚠️ <b>OGOHLANTIRISH:</b>\n"
            "Bu <b>BARCHA</b> foydalanuvchilar tomonidan generatsiya qilingan AI menyularni o'chiradi!\n\n"
            "• 🥗 Barcha AI-generatsiya qilingan meal rejalari\n\n"
            "Bu amal <b>QAYTARIB BO'LMAYDI!</b>\n\n"
            "Davom etishni xohlaysizmi?"
        )
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    
    @bot.callback_query_handler(func=lambda call: call.data == "clear_user_meals")
    def prompt_user_id_for_cleanup(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "👤 Foydalanuvchi ID-sini kiriting:\n\nMasalan: 123456789",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_user_id_cleanup, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data == "confirm_clear_ai")
    def confirm_clear_ai_callback(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        bot.answer_callback_query(call.id, "Tozalanmoqda...")
        
        try:
            # Clear only AI-generated meals
            deleted_meals = db.clear_all_meals()
            
            text = (
                "✅ <b>AI Menyu Bazasi Tozalandi!</b>\n\n"
                f"🥗 Meal rejalar: {deleted_meals} ta\n\n"
                "Barcha AI-generatsiya qilingan menyular o'chirildi."
            )
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")
        except Exception as e:
            import traceback
            traceback.print_exc()
            bot.edit_message_text(
                f"❌ Xatolik: {str(e)[:100]}",
                call.message.chat.id,
                call.message.message_id
            )
    
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_clear_ai")
    def cancel_clear_ai_callback(call):
        if call.from_user.id not in ADMIN_IDS: return
        bot.answer_callback_query(call.id)
        bot.edit_message_text("❌ Bekor qilindi.", call.message.chat.id, call.message.message_id)
    
    def process_user_id_cleanup(message, bot):
        """Process user ID and clean their AI meal data"""
        if message.from_user.id not in ADMIN_IDS:
            return
        
        try:
            user_id = int(message.text.strip())
            
            # Check if user exists
            user = db.get_user(user_id)
            if not user:
                bot.send_message(message.chat.id, f"❌ ID {user_id} bilan foydalanuvchi topilmadi.")
                return
            
            # Confirm deletion
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("✅ Ha, tozala", callback_data=f"confirm_clear_user_{user_id}"),
                types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_clear_ai")
            )
            
            user_name = user.get('full_name', 'Noma\'lum')
            text = (
                f"👤 <b>Foydalanuvchi ma'lumotlarini o'chirish</b>\n\n"
                f"ID: <code>{user_id}</code>\n"
                f"Ism: {user_name}\n\n"
                f"⚠️ Bu foydalanuvchining <b>BARCHA</b> AI menyulari o'chiriladi!\n\n"
                f"Davom etasizmi?"
            )
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
            
        except ValueError:
            bot.send_message(message.chat.id, "❌ Noto'g'ri format. Faqat raqam kiriting.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)[:100]}")
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_clear_user_"))
    def confirm_clear_user_callback(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        bot.answer_callback_query(call.id, "Tozalanmoqda...")
        
        try:
            user_id = int(call.data.replace("confirm_clear_user_", ""))
            
            # Clear user's AI meals
            deleted_count = db.clear_user_meals(user_id)
            
            text = (
                f"✅ <b>Foydalanuvchi Menyulari Tozalandi!</b>\n\n"
                f"👤 User ID: <code>{user_id}</code>\n"
                f"🥗 O'chirilgan menyular: {deleted_count} ta\n\n"
                f"Foydalanuvchining barcha AI menyulari o'chirildi."
            )
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")
        except Exception as e:
            import traceback
            traceback.print_exc()
            bot.edit_message_text(
                f"❌ Xatolik: {str(e)[:100]}",
                call.message.chat.id,
                call.message.message_id
            )
    # Helper function for flags interface (defined early for scope)
    def show_flags_interface(chat_id):
        """Helper to display flags interface - works for both commands and callbacks"""
        flags = db.get_all_feature_flags()
        
        text = "🚩 <b>Feature Flags</b>\n\n"
        markup = types.InlineKeyboardMarkup()
        
        for f in flags:
            status = "✅ ON" if f['enabled'] else "🔴 OFF"
            if f['rollout_percent'] > 0 and f['rollout_percent'] < 100:
                status += f" ({f['rollout_percent']}%)"
                
            text += f"▪️ <b>{f['key']}</b>: {status}\n"
            markup.add(types.InlineKeyboardButton(f"{f['key']} : {status}", callback_data=f"flag_edit_{f['key']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Yangi Flag", callback_data="flag_new"))
        markup.add(types.InlineKeyboardButton("🔄 Yangilash", callback_data="flag_refresh"))
        
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_flags_btn")
    def admin_flags_callback(call):
        try:
            if call.from_user.id in ADMIN_IDS:
                 bot.answer_callback_query(call.id)
                 # Call the helper function with chat_id
                 show_flags_interface(call.message.chat.id)
            else:
                 bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
        except Exception as e:
            print(f"Callback Error admin_flags: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    @bot.message_handler(func=lambda message: "Foydalanuvchi" in message.text)
    def admin_user_list(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        stats = db.get_user_stats_counts()
        
        # Show category submenu with ReplyKeyboard
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton(f"💎 Premiumlar ({stats['premium']})"),
            types.KeyboardButton(f"👑 VIP ({stats['vip']})")
        )
        markup.add(
            types.KeyboardButton(f"🆓 Bepul ({stats['free']})"),
            types.KeyboardButton(f"🎁 Triallar ({stats['trial']})")
        )
        markup.add(
            types.KeyboardButton(f"⏸ Ro'yxatdan o'tmagan ({stats['incomplete']})"),
            types.KeyboardButton(f"👥 Barcha ({stats['total']})")
        )
        markup.add(
            types.KeyboardButton("🔗 TOP 10 Referallar"),
            types.KeyboardButton("🔙 Admin Panelga")
        )
        
        bot.send_message(
            message.chat.id, 
            "👥 <b>Foydalanuvchilar Statistikasi</b>\n\nKategoriyani tanlang:",
            reply_markup=markup,
            parse_mode="HTML"
        )
    
    # Category message handlers
    @bot.message_handler(func=lambda m: "Premiumlar" in m.text and m.from_user.id in ADMIN_IDS)
    def show_premium_users(message):
        show_user_list_page(message.chat.id, 1, bot, category="premium")
    
    @bot.message_handler(func=lambda m: "VIP" in m.text and m.from_user.id in ADMIN_IDS)
    def show_vip_users(message):
        show_user_list_page(message.chat.id, 1, bot, category="vip")
    
    @bot.message_handler(func=lambda m: "Bepul" in m.text and m.from_user.id in ADMIN_IDS)
    def show_free_users(message):
        show_user_list_page(message.chat.id, 1, bot, category="free")

    @bot.message_handler(func=lambda m: "Triallar" in m.text and m.from_user.id in ADMIN_IDS)
    def show_trial_users(message):
        show_user_list_page(message.chat.id, 1, bot, category="trial")
    
    @bot.message_handler(func=lambda m: "TOP 10 Referallar" in m.text and m.from_user.id in ADMIN_IDS)
    def show_top_referrers(message):
        show_user_list_page(message.chat.id, 1, bot, category="top_ref")
    
    @bot.message_handler(func=lambda m: "Ro'yxatdan o'tmagan" in m.text and m.from_user.id in ADMIN_IDS)
    def show_incomplete_users(message):
        show_user_list_page(message.chat.id, 1, bot, category="incomplete")
    
    @bot.message_handler(func=lambda m: "Barcha" in m.text and m.from_user.id in ADMIN_IDS)
    def show_all_users(message):
        show_user_list_page(message.chat.id, 1, bot, category="all")
    
    # Orqaga button - return to admin panel
    @bot.message_handler(func=lambda m: m.text == "🔙 Admin Panelga" and m.from_user.id in ADMIN_IDS)
    def back_to_admin_panel(message):
        admin_panel(message)
    
    # Xabar yuborish submenu
    @bot.message_handler(func=lambda message: "Xabar yuborish" in message.text)
    def messaging_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("📨 Umumiy xabar"),
            types.KeyboardButton("🎯 Segment xabar")
        )
        markup.add(
            types.KeyboardButton("🛑 To'xtatish"),
            types.KeyboardButton("🔙 Admin Panelga")
        )
        
        bot.send_message(
            message.chat.id,
            "📤 <b>Xabar yuborish</b>\n\nXabar turini tanlang. Agar yuborish ketayotgan bo'lsa, 🛑 To'xtatish tugmasini bosishingiz mumkin.",
            reply_markup=markup,
            parse_mode="HTML"
        )

    @bot.message_handler(func=lambda message: message.text == "🛑 To'xtatish" and message.from_user.id in ADMIN_IDS)
    def stop_broadcast_handler(message):
        global BROADCAST_STOP
        BROADCAST_STOP = True
        bot.send_message(message.chat.id, "⏳ <b>To'xtatish so'rovi yuborildi...</b>\nJarayon keyingi batchda to'xtaydi.", parse_mode="HTML")

    # User Deletion Handlers
    @bot.message_handler(func=lambda message: "Userni o'chirish" in message.text)
    def ask_user_delete_start(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(
            message.chat.id, 
            "🛑 <b>Foydalanuvchini O'chirish</b>\n\n"
            "O'chirilishi kerak bo'lgan foydalanuvchining <b>Telegram ID</b> sini yozing:\n"
            "(Masalan: 123456789)",
            parse_mode="HTML",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_user_delete_id, bot)

    def process_user_delete_id(message, bot):
        if message.from_user.id not in ADMIN_IDS: return
        
        try:
            target_id = int(message.text.strip())
            user = db.get_user(target_id)
            
            if not user:
                bot.send_message(message.chat.id, "❌ Bunday ID bilan foydalanuvchi topilmadi.")
                return

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Ha, o'chirilsin", callback_data=f"hard_delete_{target_id}"),
                types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_delete")
            )
            
            fullname = user.get('full_name', 'Noma\'lum')
            username = f"@{user.get('username')}" if user.get('username') else "Yo'q"
            
            text = (
                f"🛑 <b>DIQQAT! O'chirishni tasdiqlang.</b>\n\n"
                f"👤 Ism: {fullname}\n"
                f"🔗 Link: {username}\n"
                f"🆔 ID: <code>{target_id}</code>\n\n"
                f"⚠️ <b>Bu amal:</b>\n"
                f"- Profilni o'chiradi\n"
                f"- Barcha loglarni tozalaydi\n"
                f"- Obunalarni bekor qiladi\n"
                f"- Qaytarib bo'lmaydi!\n\n"
                f"Rostdan ham o'chirasizmi?"
            )
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
            
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID raqam bo'lishi kerak.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("hard_delete_"))
    def execute_user_delete(call):
        if call.from_user.id not in ADMIN_IDS: return
        
        try:
            target_id = int(call.data.replace("hard_delete_", ""))
            bot.edit_message_text(f"⏳ O'chirilmoqda... ID: {target_id}", call.message.chat.id, call.message.message_id)
            
            success, msg = db.delete_user_by_id(target_id)
            
            if success:
                bot.send_message(call.message.chat.id, f"✅ <b>Bajarildi:</b>\n{msg}", parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, f"❌ <b>Xatolik:</b>\n{msg}", parse_mode="HTML")
                
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Kritik Xatolik: {e}")

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
    def cancel_delete_process(call):
        if call.from_user.id not in ADMIN_IDS: return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Bekor qilindi")


    def show_user_list_page(chat_id, page, bot, message_id=None, category="all"):
        try:
            PAGE_SIZE = 10
            
            #Get filtered users based on category
            if category == "premium":
                users, total_count = db.get_premium_users_paginated(page, PAGE_SIZE)
                cat_title = "💎 Premium"
            elif category == "vip":
                users, total_count = db.get_vip_users_paginated(page, PAGE_SIZE)
                cat_title = "👑 VIP"
            elif category == "free":
                users, total_count = db.get_free_users_paginated(page, PAGE_SIZE)
                cat_title = "🆓 Bepul"
            elif category == "trial":
                users, total_count = db.get_trial_users_paginated(page, PAGE_SIZE)
                cat_title = "🎁 Trial"
            elif category == "top_ref":
                users, total_count = db.get_top_referrers(10), 10
                cat_title = "🔗 TOP 10 Referallar"
            elif category == "incomplete":
                users, total_count = db.get_incomplete_users_paginated(page, PAGE_SIZE)
                cat_title = "⏸ Ro'yxatdan o'tmagan"
            else: # all
                users, total_count = db.get_users_paginated(page, PAGE_SIZE)
                cat_title = "👥 Barcha"
            
            if not users:
                text = "👥 Foydalanuvchilar topilmadi."
                if message_id:
                    bot.edit_message_text(text, chat_id, message_id)
                else:
                    bot.send_message(chat_id, text)
                return

            total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
            
            text = f"{cat_title} <b>Foydalanuvchilar</b> (Jami: {total_count})\nSahifa: {page}/{total_pages}\n\n"
            
            for i, user in enumerate(users, 1):
                uid = user.get('telegram_id', 'N/A')
                name = user.get('full_name') or "N/A"
                username = user.get('username')
                phone = user.get('phone') or "N/A"
                goal = user.get('goal') or "N/A"
                gender = user.get('gender') or "N/A"
                age = user.get('age') or "N/A"
                height = user.get('height') or "N/A"
                weight = user.get('weight') or "N/A"
                activity = user.get('activity_level') or "N/A"
                
                # Translations
                goal_map = {
                    "weight_loss": "Vazn tashlash 🔻",
                    "muscle_gain": "Vazn olish 🔺",
                    "health": "Vazn saqlash ❤️",
                    "N/A": "-"
                }
                gender_map = {"male": "👨 Erkak", "female": "👩 Ayol", "N/A": "-"}
                activity_map = {
                    "sedentary": "Kam harakatli",
                    "light": "Yengil faol",
                    "active": "Faol",
                    "athlete": "Atlet",
                    "N/A": "-"
                }
                
                formatted_goal = goal_map.get(goal, goal)
                formatted_gender = gender_map.get(gender, gender)
                formatted_activity = activity_map.get(activity, activity)

                # Plan check
                plan_badge = ""
                if user.get('premium_until'):
                    from datetime import datetime
                    prem_until = user['premium_until']
                    if isinstance(prem_until, str):
                        try: prem_until = datetime.fromisoformat(prem_until.replace('Z', '+00:00'))
                        except: prem_until = None
                    
                    if prem_until and isinstance(prem_until, datetime) and prem_until > datetime.now():
                        if user.get('plan_type') == 'trial':
                            plan_badge = " 🎁 Trial"
                        elif user.get('plan_type') == 'vip':
                            plan_badge = " 👑 VIP"
                        else:
                            plan_badge = " 💎 Premium"
                
                display_name = f"@{username}" if username else name
                
                # Registration and Last Activity
                reg_date = user.get('created_at')
                last_act = user.get('updated_at')
                
                reg_str = reg_date.strftime("%Y-%m-%d") if hasattr(reg_date, 'strftime') else "-"
                act_str = last_act.strftime("%Y-%m-%d %H:%M") if hasattr(last_act, 'strftime') else "-"
                
                # Compact but comprehensive display
                text += f"<b>{i}. {display_name}</b>{plan_badge}\n"
                text += f"   🆔 ID: <code>{uid}</code>\n"
                text += f"   📱 Tel: {phone}\n"
                text += f"   🎯 Maqsad: {formatted_goal}\n"
                text += f"   {formatted_gender} | {age} yosh | {height}cm / {weight}kg\n"
                text += f"   🏃 Faollik: {formatted_activity}\n"
                text += f"   📅 Reg: {reg_str} | 🕒 Aktiv: {act_str}\n\n"
            
            # Pagination + Search Buttons
            markup = types.InlineKeyboardMarkup()
            row = []
            if page > 1:
                row.append(types.InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_users_page_{page-1}"))
            if page < total_pages:
                row.append(types.InlineKeyboardButton("Keyingi ➡️", callback_data=f"admin_users_page_{page+1}"))
            
            if row:
                markup.row(*row)
            
            # Add ID Search button
            markup.add(types.InlineKeyboardButton("🔍 ID bo'yicha qidirish", callback_data="admin_search_user_id"))
            
            if message_id:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
                
        except Exception as e:
            print(f"Error in user list: {e}")
            import traceback
            traceback.print_exc()
            error_text = f"❌ Xatolik: {str(e)[:100]}"
            if message_id:
                bot.send_message(chat_id, error_text)
            else:
                bot.send_message(chat_id, error_text)

    # Category handlers
    @bot.callback_query_handler(func=lambda call: call.data.startswith("users_cat_"))
    def handle_user_category(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        bot.answer_callback_query(call.id)
        category = call.data.replace("users_cat_", "")
        
        # Show first page of selected category
        show_user_list_page(call.message.chat.id, 1, bot, message_id=call.message.message_id, category=category)
    
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
    
    @bot.callback_query_handler(func=lambda call: call.data == "admin_search_user_id")
    def handle_search_user_id(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "🔍 <b>Foydalanuvchini ID bo'yicha qidirish</b>\n\nTelegram ID ni kiriting:",
            parse_mode="HTML",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_user_id_search, bot)
    
    def process_user_id_search(message, bot):
        """Handle ID search input"""
        if message.from_user.id not in ADMIN_IDS:
            return
        
        try:
            user_id = int(message.text.strip())
            user = db.get_user(user_id)
            
            if not user:
                bot.send_message(message.chat.id, f"❌ Foydalanuvchi ID <code>{user_id}</code> topilmadi.", parse_mode="HTML")
                return
            
            # Display full user profile
            name = user.get('full_name', 'N/A')
            username = user.get('username', 'N/A')
            phone = user.get('phone', 'N/A')
            goal = user.get('goal', 'N/A')
            gender = user.get('gender', 'N/A')
            age = user.get('age', 'N/A')
            height = user.get('height', 'N/A')
            weight = user.get('weight', 'N/A')
            activity = user.get('activity_level', 'N/A')
            premium_until = user.get('premium_until')
            
            # Translations
            goal_map = {"weight_loss": "Vazn tashlash", "muscle_gain": "Vazn olish", "health": "Vazn saqlash", "N/A": "-"}
            gender_map = {"male": "Erkak", "female": "Ayol", "N/A": "-"}
            activity_map = {"sedentary": "Kam harakatli", "light": "Yengil faol", "active": "Faol", "athlete": "Atlet", "N/A": "-"}
            
            premium_status = "Yo'q"
            if premium_until:
                from datetime import datetime
                # Defensive check for string types
                if isinstance(premium_until, str):
                    try: premium_until = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
                    except: premium_until = None

                if premium_until and isinstance(premium_until, datetime) and premium_until > datetime.now():
                    premium_status = f"✅ {premium_until.strftime('%Y-%m-%d')}"
            
            text = (
                f"👤 <b>Foydalanuvchi profili</b>\n\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"👤 Ism: {name}\n"
                f"📝 Username: @{username if username != 'N/A' else '-'}\n"
                f"📱 Telefon: {phone}\n\n"
                f"<b>Profil ma'lumotlari:</b>\n"
                f"🎯 Maqsad: {goal_map.get(goal, goal)}\n"
                f"👥 Jins: {gender_map.get(gender, gender)}\n"
                f"🎂 Yosh: {age} yosh\n"
                f"📏 Bo'y: {height} cm\n"
                f"⚖️ Vazn: {weight} kg\n"
                f"🏃 Faollik: {activity_map.get(activity, activity)}\n\n"
                f"💎 Premium: {premium_status}"
            )
            
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            
        except ValueError:
            lang = db.get_user_language(message.from_user.id)
            bot.send_message(message.chat.id, get_text("error_only_numbers", lang))
        except Exception as e:
            print(f"Search error: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)[:100]}")

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
    def admin_broadcast_simple(message):
        """Simple broadcast - just send to all users"""
        if message.from_user.id not in ADMIN_IDS:
            return
        
        print(f"DEBUG: Simple broadcast by {message.from_user.id}")
        try:
            msg = bot.send_message(
                message.chat.id, 
                "📨 <b>Umumiy xabar</b>\n\nBarcha foydalanuvchilarga xabar yuboring:\n(matn, rasm, video)", 
                reply_markup=types.ForceReply(),
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, process_broadcast, bot, "all")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
    
    # Advanced broadcast with segment options (for Developer menu)
    def admin_broadcast_start(message):
        """Advanced broadcast - with segment selection"""
        if message.from_user.id not in ADMIN_IDS:
            return
        
        print(f"DEBUG: Advanced broadcast by {message.from_user.id}")
        try:
            # Show segment selection
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👥 Barcha foydalanuvchilar", callback_data="broadcast_all"))
            markup.add(types.InlineKeyboardButton("💎 Premium foydalanuvchilar", callback_data="broadcast_premium"))
            markup.add(types.InlineKeyboardButton("🆓 Bepul foydalanuvchilar", callback_data="broadcast_free"))
            
            bot.send_message(
                message.chat.id,
                "📢 <b>Broadcast</b>\n\nQaysi segmentga xabar yubormoqchisiz?",
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
    
    # Broadcast segment selection callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith("broadcast_"))
    def handle_broadcast_segment(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        segment = call.data.replace("broadcast_", "")  # all, premium, or free
        bot.answer_callback_query(call.id)
        
        msg = bot.send_message(
            call.message.chat.id,
            f"📤 Xabarni yuboring ({segment} segment uchun):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_broadcast, bot, segment)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('dev_'))
    def dev_main_callback_handler(call):
        if call.from_user.id not in ADMIN_IDS: return
        
        action = call.data
        bot.answer_callback_query(call.id)
        
        # Spoofing from_user to bypass permission check in command functions
        msg = call.message
        msg.from_user = call.from_user
        
        if action == "dev_clear_ai_db":
             admin_clear_ai_data(msg)
        elif action == "dev_delete_user_start":
             ask_user_delete_start(msg)
        elif action == "dev_test_ai_start":
             admin_test_ai(msg)
        elif action == "dev_flags_menu":
             show_flags_interface(msg.chat.id)
        elif action == "dev_broadcast_menu":
             messaging_menu(msg)
        elif action == "dev_stats_old":
             admin_stats(msg)




    @bot.message_handler(func=lambda message: "Segment xabar" in message.text)
    def admin_segment_start(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # 1. Obuna turi
        markup.row(types.InlineKeyboardButton("💳 --- OBUNA TURI ---", callback_data="none"))
        markup.add(
            types.InlineKeyboardButton("🆓 Bepul", callback_data="seg_plan_type_free"),
            types.InlineKeyboardButton("🎁 Trial", callback_data="seg_plan_type_trial"),
            types.InlineKeyboardButton("💎 Premium", callback_data="seg_plan_type_premium"),
            types.InlineKeyboardButton("👑 VIP", callback_data="seg_plan_type_vip")
        )
        
        # 2. Til bo'yicha
        markup.row(types.InlineKeyboardButton("🌐 --- TIL BO'YICHA ---", callback_data="none"))
        markup.add(
            types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="seg_language_uz"),
            types.InlineKeyboardButton("🇷🇺 Ruscha", callback_data="seg_language_ru")
        )
        
        # 3. Demografiya
        markup.row(types.InlineKeyboardButton("👤 --- DEMOGRAFIYA ---", callback_data="none"))
        markup.add(
            types.InlineKeyboardButton("👨 Erkaklar", callback_data="seg_gender_male"),
            types.InlineKeyboardButton("👩 Ayollar", callback_data="seg_gender_female")
        )
        
        # 4. Maqsad
        markup.row(types.InlineKeyboardButton("🎯 --- MAQSAD ---", callback_data="none"))
        markup.add(
            types.InlineKeyboardButton("🔻 Ozish", callback_data="seg_goal_weight_loss"),
            types.InlineKeyboardButton("🔺 Massa", callback_data="seg_goal_muscle_gain"),
            types.InlineKeyboardButton("❤️ Salomatlik", callback_data="seg_goal_health")
        )
        
        # 5. Faollik
        markup.row(types.InlineKeyboardButton("⏳ --- FAOLLIK ---", callback_data="none"))
        markup.add(
            types.InlineKeyboardButton("😴 7 kundan beri kirmagan", callback_data="seg_inactive_days_7"),
            types.InlineKeyboardButton("👻 30 kundan beri kirmagan", callback_data="seg_inactive_days_30")
        )
        
        # 6. Onboarding
        markup.row(types.InlineKeyboardButton("📝 --- RO'YXATDAN O'TISH ---", callback_data="none"))
        markup.add(
            types.InlineKeyboardButton("✅ Tugatganlar", callback_data="seg_is_onboarded_True"),
            types.InlineKeyboardButton("⚠️ Tugatmaganlar", callback_data="seg_is_onboarded_False")
        )
        
        bot.send_message(
            message.chat.id, 
            "🎯 <b>Segmentni tanlang:</b>\n\nXabar faqat tanlangan guruhga yuboriladi.", 
            reply_markup=markup,
            parse_mode="HTML"
        )

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
    global BROADCAST_STOP
    BROADCAST_STOP = False # Reset stop flag
    
    try:
        # Check if user cancelled
        if message.text and message.text.startswith("/"):
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")
            return

        # Setup filter args
        filter_args = {}
        if segment != "all":
            key, value = segment[0], segment[1]
            if value == "True": value = True
            elif value == "False": value = False
            elif key == "inactive_days": value = int(value)
            filter_args[key] = value

        # 1. Total Count (for progress bar)
        if segment == "all":
            total_users = db.get_active_users_count()
        else:
            # We need a new method for count or just estimate/fetch all for small counts
            # Since get_active_users_batch is used, let's just use it to find the end.
            # But for progress bar we need TOTAL.
            # Let's add a quick count logic or just fetch all IDs first (might be heavy for 100k+, but okay for a few thousands)
            # Better: query.count() in a new method.
            # For now, let's just show "Processing..." without % if total unknown.
            # Or assume we can get total from db.
            total_users = db.get_segment_users_count(**filter_args) if segment != "all" else db.get_active_users_count()

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
        while True:
            if BROADCAST_STOP:
                bot.send_message(message.chat.id, "🛑 <b>Broadcast to'xtatildi!</b>", parse_mode="HTML")
                break

            # Fetch batch
            if segment == "all":
                users_batch_data = db.get_active_users_batch(offset=offset, limit=BATCH_SIZE)
            else:
                users_batch_data = db.get_users_by_segment_batch(**filter_args, offset=offset, limit=BATCH_SIZE)

            if not users_batch_data:
                break # No more users
            
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
                
            # Update status every batch
            elapsed = int(time.time() - start_time)
            
            # Progress Bar logic
            progress_text = ""
            if total_users > 0:
                percent = int((success + failed) / total_users * 100)
                filled = int(percent / 10)
                bar = "🟩" * filled + "⬜️" * (10 - filled)
                progress_text = f"\n{bar} {percent}%"
            
            status_text = (
                f"📡 <b>Xabar yuborilmoqda...</b>\n"
                f"{progress_text}\n\n"
                f"✅ Muvaffaqiyatli: {success}\n"
                f"❌ Yetib bormadi: {failed}\n"
                f"👥 Jami target: {total_users}\n"
                f"⏱ Sarflangan vaqt: {elapsed}s"
            )
            
            # Add stop button in status? Only if we want to constantly update markup.
            # For now, just text update.
            try:
                bot.edit_message_text(status_text, message.chat.id, status_msg_id, parse_mode="HTML")
            except: pass
            
            offset += BATCH_SIZE
            time.sleep(1) # Rate limit
            
        bot.send_message(
            message.chat.id, 
            f"🏁 <b>Broadcast tugadi!</b>\n\n✅: {success}\n❌: {failed}\n⏱: {int(time.time() - start_time)}s",
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"Error in process_broadcast: {e}")
        import traceback
        traceback.print_exc()
        try:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
        except: pass



# === Subscription Management ===

def register_subscription_handlers(bot):
    @bot.message_handler(func=lambda message: "Obunalar" in message.text and message.from_user.id in ADMIN_IDS)
    def admin_subs_start(message):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Foydalanuvchi qidirish", callback_data="sub_search"))
        markup.add(types.InlineKeyboardButton("🎁 Barchaga 14 kunlik Trial", callback_data="sub_mass_trial"))
        bot.send_message(message.chat.id, "💳 **Obunalar boshqaruvi**\n\nQuyidagilardan birini tanlang:", reply_markup=markup, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "sub_search")
    def sub_search_callback(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🔍 **Foydalanuvchi qidirish**\n\nIltimos, foydalanuvchi ID raqamini yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_subs_user_id, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "sub_mass_trial")
    def sub_mass_trial_callback(call):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="sub_mass_trial_confirm"),
            types.InlineKeyboardButton("❌ Bekor qilish", callback_data="sub_mass_trial_cancel")
        )
        bot.edit_message_text(
            "⚠️ **DIQQAT!**\n\nUshbu amal barcha foydalanuvchilarning obunasini bekor qiladi va har biriga **14 kunlik Trial** beradi.\n\nHaqiqatan ham davom ettirmoqchimisiz?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data == "sub_mass_trial_confirm")
    def sub_mass_trial_confirm_callback(call):
        bot.edit_message_text("⏳ Amallar bajarilmoqda, iltimos kuting...", call.message.chat.id, call.message.message_id)
        
        try:
            users, subs = db.mass_reset_to_trial(days=14)
            bot.edit_message_text(
                f"✅ **Muvaffaqiyatli bajarildi!**\n\n- {users} ta foydalanuvchiga 14 kunlik trial berildi.\n- {subs} ta faol obuna to'xtatildi.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.edit_message_text(f"❌ Xatolik yuz berdi: {e}", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "sub_mass_trial_cancel")
    def sub_mass_trial_cancel_callback(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "❌ Amal bekor qilindi.")

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
        print(f"DEBUG: handle_sub_action triggered for {call.data}")
        try:
            bot.answer_callback_query(call.id)
        except: pass

        if call.from_user.id not in ADMIN_IDS:
            return
            
        action, target_id = call.data.split("_")[1], int(call.data.split("_")[2])
        
        if action == "reset":
            db.reset_user_ai_limits(target_id)
            bot.send_message(call.message.chat.id, "✅ Limitlar 0 ga tushirildi!")
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

    @bot.message_handler(commands=['clear_meals'])
    def admin_clear_meals_start(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(
            message.chat.id, 
            "⚠️ <b>DIQQAT!</b>\n\nBu buyruq BARCHA foydalanuvchilarning eski AI ovqat rejalarini o'chirib yuboradi.\nUlarga yangi menyular kerak bo'lganda qaytadan generatsiya qilishadi.\n\nDavom etish uchun <code>TASDIQLAYMAN</code> deb yozing:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_clear_meals_confirmation, bot)

    def process_clear_meals_confirmation(message, bot):
        if message.text == "TASDIQLAYMAN":
            count = db.clear_all_meals()
            bot.send_message(message.chat.id, f"✅ Bajarildi! {count} ta eski ovqat rejasi o'chirib yuborildi.")
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


def generate_analytics_report():
    from backend.database import get_sync_db
    from sqlalchemy import text
    from datetime import datetime
    
    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    with get_sync_db() as session:
        # 1. DAU / WAU / MAU
        dau = session.execute(text("SELECT COUNT(DISTINCT user_id) FROM event_logs WHERE created_at >= date_trunc('day', now()) AND created_at < date_trunc('day', now()) + interval '1 day'")).scalar() or 0
        wau = session.execute(text("SELECT COUNT(DISTINCT user_id) FROM event_logs WHERE created_at >= now() - interval '7 days'")).scalar() or 0
        mau = session.execute(text("SELECT COUNT(DISTINCT user_id) FROM event_logs WHERE created_at >= now() - interval '30 days'")).scalar() or 0
        
        stickiness = round((dau / mau * 100), 1) if mau > 0 else 0
        
        # 2. Retention (Cohort: onboarding_completed) - Simplified for robustness
        # Note: Needs strictly defined 'onboarding_completed' event to be accurate.
        # Fallback to 'start' or similar if onboarding event new.
        ret_sql = """
        WITH cohort AS (
          SELECT user_id, MIN(date_trunc('day', created_at)) AS day0
          FROM event_logs
          WHERE event_type = 'onboarding_completed'
            AND created_at >= now() - interval '30 days'
          GROUP BY 1
        ),
        activity AS (
          SELECT DISTINCT user_id, date_trunc('day', created_at) AS day
          FROM event_logs
          WHERE created_at >= now() - interval '30 days'
        ),
        ret AS (
          SELECT
            c.day0,
            c.user_id,
            EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '1 day') AS d1,
            EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '3 day') AS d3,
            EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '7 day') AS d7
          FROM cohort c
        )
        SELECT
          COUNT(*) AS cohort_size,
          ROUND(100.0 * SUM(CASE WHEN d1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d1,
          ROUND(100.0 * SUM(CASE WHEN d3 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d3,
          ROUND(100.0 * SUM(CASE WHEN d7 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d7
        FROM ret;
        """
        try:
            ret_res = session.execute(text(ret_sql)).fetchone()
            d1, d3, d7 = (ret_res.d1, ret_res.d3, ret_res.d7) if ret_res else (0,0,0)
        except:
             d1, d3, d7 = 0, 0, 0

        # 3. Conversion
        conv_sql = """
        WITH trial AS (
          SELECT DISTINCT user_id FROM event_logs WHERE event_type = 'trial_started' AND created_at >= now() - interval '30 days'
        ),
        paid AS (
          SELECT DISTINCT user_id FROM event_logs WHERE event_type = 'premium_activated' AND created_at >= now() - interval '30 days'
        )
        SELECT
          (SELECT COUNT(*) FROM trial) AS trial_users,
          (SELECT COUNT(*) FROM paid) AS paid_users
        """
        conv_res = session.execute(text(conv_sql)).fetchone()
        trial_users = conv_res.trial_users
        paid_users = conv_res.paid_users
        try:
             trial_to_paid = round((paid_users / trial_users * 100), 1) if trial_users > 0 else 0
        except: trial_to_paid = 0

        # 4. Funnel Drop-off (Last 7 days)
        # Assuming events exist. If purely logic-based counters implementation, these will be 0 initially.
        funnel_menu = session.execute(text("SELECT COUNT(*) FROM event_logs WHERE event_type='menu_generated' AND created_at >= now() - interval '7 days'")).scalar() or 0
        funnel_shop = session.execute(text("SELECT COUNT(*) FROM event_logs WHERE event_type='shopping_list_opened' AND created_at >= now() - interval '7 days'")).scalar() or 0
        no_shopping_users = funnel_menu - funnel_shop
        no_shopping_pct = round((no_shopping_users / funnel_menu * 100), 1) if funnel_menu > 0 else 0
        
        # 5. Feature Usage (Today)
        feats_sql = """
        SELECT
          COUNT(*) FILTER (WHERE event_type='menu_generated') AS menu_gen,
          COUNT(*) FILTER (WHERE event_type='workout_generated') AS workout_gen,
          COUNT(*) FILTER (WHERE event_type='calorie_scanned') AS calorie_scans,
          COUNT(*) FILTER (WHERE event_type='coach_message_generated') AS coach_views
        FROM event_logs
        WHERE created_at >= date_trunc('day', now())
        """
        feat_res = session.execute(text(feats_sql)).fetchone()
        
        # 6. UTM
        utm_sql = "SELECT utm_source, COUNT(*) AS users FROM users WHERE utm_source IS NOT NULL GROUP BY utm_source ORDER BY users DESC LIMIT 5"
        utm_rows = session.execute(text(utm_sql)).fetchall()
        utm_lines = "\n".join([f"• {u.utm_source}: {u.users}" for u in utm_rows]) if utm_rows else "• (Ma'lumot yo'q)"

        msg = f"""<b>📊 YASHA Analytics (Pro)</b>
🕒 {now_ts}

<b>1) Aktivlik</b>
• DAU (bugun): {dau}
• WAU (7 kun): {wau}
• MAU (30 kun): {mau}
• Stickiness: {stickiness}%

<b>2) Retention (Cohort)</b>
• D1: {d1}%
• D3: {d3}%
• D7: {d7}%

<b>3) Konversiya</b>
• Trial users: {trial_users}
• Paid users: {paid_users}
• Trial → Paid: {trial_to_paid}%

<b>4) Funnel drop-off (7 kun)</b>
• Menu generated: {funnel_menu}
• Shopping opened: {funnel_shop}
• No shopping: {no_shopping_users} ({no_shopping_pct}%)

<b>5) Feature usage (bugun)</b>
• 🍽 Menyu: {feat_res.menu_gen}
• 🏋️ Mashq: {feat_res.workout_gen}
• 📸 Kaloriya skan: {feat_res.calorie_scans}
• 💬 Coach zone: {feat_res.coach_views}

<b>6) Top UTM Sources</b>
{utm_lines}
"""
        return msg

def generate_menu_rollout_report():
    from backend.database import get_sync_db
    from sqlalchemy import text
    from datetime import datetime
    
    with get_sync_db() as session:
        # Last 24h stats
        sql = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE (meta::jsonb->>'source') IN ('LOCAL', 'CACHE')) as local_count,
            COUNT(*) FILTER (WHERE (meta::jsonb->>'source') = 'AI') as ai_count,
            COUNT(*) FILTER (WHERE (meta::jsonb->>'is_fallback')::boolean = true) as fallback_count
        FROM admin_events
        WHERE event_type = 'MENU_GENERATION'
          AND created_at >= now() - interval '24 hours'
        """
        try:
            res = session.execute(text(sql)).fetchone()
            total = res.total or 0
            local = res.local_count or 0
            ai = res.ai_count or 0
            fallback = res.fallback_count or 0
        except:
            total = local = ai = fallback = 0
        
        # Fallback reasons
        reason_sql = """
        SELECT (meta::jsonb->>'fallback_reason') as reason, COUNT(*) as count
        FROM admin_events
        WHERE event_type = 'MENU_GENERATION'
          AND (meta::jsonb->>'is_fallback')::boolean = true
          AND created_at >= now() - interval '24 hours'
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 5
        """
        try:
            reasons = session.execute(text(reason_sql)).fetchall()
        except:
            reasons = []
        
        # Token usage (Menu feature only)
        token_sql = """
        SELECT SUM(input_tokens + output_tokens) as total_tokens, SUM(cost_usd) as total_cost
        FROM ai_usage_logs
        WHERE feature IN ('menu', 'menu_advice')
          AND timestamp >= now() - interval '24 hours'
        """
        try:
            tokens = session.execute(text(token_sql)).fetchone()
            total_tokens = tokens.total_tokens or 0
            total_cost = tokens.total_cost or 0
        except:
            total_tokens = 0
            total_cost = 0
        
    local_pct = (local / total * 100) if total > 0 else 0
    ai_pct = (ai / total * 100) if total > 0 else 0
    
    txt = "🥗 <b>Menu Rollout Analytics (Last 24h)</b>\n\n"
    txt += f"📊 Total Generations: {total}\n"
    txt += f"✅ LOCAL (DB+Cache): {local} ({local_pct:.1f}%)\n"
    txt += f"🤖 AI Generator: {ai} ({ai_pct:.1f}%)\n"
    txt += f"⚠️ Fallbacks: {fallback}\n\n"
    
    if reasons:
        txt += "<b>Top Fallback Reasons:</b>\n"
        for r in reasons:
            txt += f"• {r.reason or 'Unknown'}: {r.count}\n"
        txt += "\n"
        
    txt += "<b>AI Costs (Menu Only):</b>\n"
    txt += f"• Tokens: {total_tokens:,}\n"
    txt += f"• Estimated Cost: ${total_cost:.4f}\n"
    
    return txt



def generate_workout_rollout_report():
    """Fetches stats for WORKOUT_GENERATION events in the last 24h."""
    from backend.database import get_sync_db
    from sqlalchemy import text
    import json
    
    with get_sync_db() as session:
        # Total generations
        total_sql = "SELECT COUNT(*) FROM admin_events WHERE event_type = 'WORKOUT_GENERATION' AND created_at >= now() - interval '24 hours'"
        total = session.execute(text(total_sql)).scalar() or 0
        
        if total == 0:
            return "🏋️ <b>Workout Rollout Analytics (Last 24h)</b>\n\nNo workout generations recorded yet."
        
        # Source distribution
        source_sql = """
        SELECT meta::json->>'source' as src, COUNT(*) as cnt 
        FROM admin_events 
        WHERE event_type = 'WORKOUT_GENERATION' AND created_at >= now() - interval '24 hours'
        GROUP BY src
        """
        sources = session.execute(text(source_sql)).fetchall()
        
        counts = {"DB": 0, "AI": 0, "CACHE": 0}
        for src, cnt in sources:
            if src in counts: counts[src] += cnt
        
        db_count = counts["DB"] + counts["CACHE"]
        ai_count = counts["AI"]
        
        # Fallbacks
        fallback_sql = """
        SELECT COUNT(*) FROM admin_events 
        WHERE event_type = 'WORKOUT_GENERATION' 
          AND meta::json->>'is_fallback' = 'true'
          AND created_at >= now() - interval '24 hours'
        """
        fallbacks = session.execute(text(fallback_sql)).scalar() or 0
        
        # Top fallback reasons
        reason_sql = """
        SELECT meta::json->>'fallback_reason' as reason, COUNT(*) as cnt
        FROM admin_events
        WHERE event_type = 'WORKOUT_GENERATION'
          AND meta::json->>'is_fallback' = 'true'
          AND created_at >= now() - interval '24 hours'
        GROUP BY reason
        ORDER BY cnt DESC LIMIT 5
        """
        reasons = session.execute(text(reason_sql)).fetchall()
        
        reasons_text = ""
        if reasons:
            reasons_text = "\n\n<b>Top Fallback Reasons:</b>\n" + "\n".join([f"• {r[0]}: {r[1]}" for r in reasons])

        # AI Costs (Workout Only)
        token_sql = """
        SELECT SUM(input_tokens + output_tokens) as total_tokens, SUM(cost_usd) as total_cost
        FROM ai_usage_logs
        WHERE feature IN ('workout', 'workout_motivation')
          AND timestamp >= now() - interval '24 hours'
        """
        try:
            tokens_res = session.execute(text(token_sql)).fetchone()
            total_tokens = tokens_res[0] or 0
            total_cost = tokens_res[1] or 0
        except:
            total_tokens, total_cost = 0, 0

        msg = f"🏋️ <b>Workout Rollout Analytics (Last 24h)</b>\n\n"
        msg += f"📊 Total Generations: {total}\n"
        msg += f"✅ DB (Local+Cache): {db_count} ({round(db_count/total*100, 1)}%)\n"
        msg += f"🤖 AI Generator: {ai_count} ({round(ai_count/total*100, 1)}%)\n"
        msg += f"⚠️ Fallbacks: {fallbacks}"
        msg += reasons_text
        msg += f"\n\n<b>AI Costs (Workout Only):</b>\n"
        msg += f"• Tokens: {total_tokens:,}\n"
        msg += f"• Estimated Cost: ${total_cost:.4f}"
        
        return msg

