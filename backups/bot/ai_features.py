from telebot import types
from core.ai import call_gemini, format_gemini_text
from core.db import db
from bot.premium import require_premium

from bot.keyboards import ai_inline_keyboard

def handle_ai_tools_menu(message, bot):
    with open("assets/ai_murabbiy.png", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption="<b>🤖 AI shaxsiy murabbiy</b>\n\nMaqsadingizga tezroq yetishingizga yordam beraman.\nTayyormisiz? — Keyingi qadamni tanlang👇🏻",
            reply_markup=ai_inline_keyboard(),
            parse_mode="HTML"
        )

@require_premium
def handle_ai_qa(message, bot, user_id=None):
    try:
        msg = bot.send_message(
            message.chat.id, 
            "❓ <b>AI Murabbiy</b>\n\nMashg'ulotlar, ovqatlanish yoki sog'lom turmush tarzi bo'yicha istalgan savolingizni yozing:", 
            reply_markup=types.ForceReply(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_ai_qa, bot)
    except Exception as e:
        print(f"Handle AI QA Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_ai_qa(message, bot):
    user_id = message.from_user.id
    if not message.text:
        bot.send_message(user_id, "Iltimos, savolingizni matn ko'rinishida yozing.")
        return
        
    question = message.text
    user = db.get_user(user_id)
    
    # Send "typing" action instead of message to avoid clutter, or keep message if preferred
    status_msg = bot.send_message(user_id, "🤖 <b>Javob tayyorlanmoqda...</b>", parse_mode="HTML")
    
    system_prompt = f"""
    Siz professional fitnes murabbiyisiz.
    
    Foydalanuvchi Profili:
    - Yosh: {user.get('age')}
    - Jins: {user.get('gender')}
    - Bo'y: {user.get('height')} sm
    - Vazn: {user.get('weight')} kg
    - Maqsad: {user.get('goal')}
    - Faollik: {user.get('activity_level')}
    
    Vazifa: Savolga qisqa, aniq va foydalanuvchi profiliga moslashtirilgan javob bering.
    
    FORMAT TALABLARI:
    - Maksimal 700-900 belgi.
    - Qisqa paragraflar.
    - Muhim joylari uchun <b>qalin</b> (HTML) ishlating.
    - Ro'yxat uchun tire (-) ishlating.
    - Markdown ishlata ko'rmang (* yoki _).
    - Faqat HTML teglar: <b>, <i>, <u>, <s>, <code>, <pre>.
    - O'zbek tilida.
    """
    
    try:
        from core.ai import ask_gemini
        response = ask_gemini(system_prompt, question)
        
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            log_ai_usage(bot, user_id, "chat", 150)
        except: pass
        
        # Edit status message with response
        try:
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode="HTML")
        except Exception:
            # Fallback to plain text if HTML is invalid
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode=None)
            
        # Send main menu to restore navigation
        from bot.keyboards import main_menu_keyboard
        bot.send_message(user_id, "Yana nima yordam bera olaman?", reply_markup=main_menu_keyboard())
            
    except Exception as e:
        print(f"AI QA Error: {e}")
        bot.edit_message_text("AI hozircha javob bera olmadi. Birozdan keyin yana urinib ko‘ring 🙂", user_id, status_msg.message_id)

@require_premium
def handle_shopping_list(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    # 1. Check for existing Menu Link
    active_link = db.get_user_menu_link(user_id)
    
    if not active_link:
        bot.send_message(user_id, "⚠️ Sizda hali menyu yo'q.\n\nIltimos, avval <b>AI ovqatlanish rejasi</b>ni tuzing.", parse_mode="HTML")
        return

    # 2. Get Shopping List from Link
    try:
        import json
        shopping_list = json.loads(active_link['shopping_list_json'])
        
        if not shopping_list:
            bot.send_message(user_id, "⚠️ Xaridlar ro'yxati bo'sh.", parse_mode="HTML")
            return
            
        # 3. Format and Send
        txt = "🛒 <b>30 KUNLIK XARIDLAR RO'YXATI</b>\n\n"
        txt += "<i>(Sizning joriy menyuingiz asosida)</i>\n\n"
        
        for item in shopping_list:
            txt += f"▫️ {item}\n"
            
        bot.send_message(user_id, txt, parse_mode="HTML")
        
    except Exception as e:
        print(f"Shopping List Error: {e}")
        bot.send_message(user_id, "⚠️ Xatolik yuz berdi. Iltimos, qayta menyu tuzing.")

@require_premium
def handle_recipe_gen(message, bot, user_id=None):
    try:
        msg = bot.send_message(
            message.chat.id, 
            "🍳 <b>AI Retsept</b>\n\nMuzlatgichda bor mahsulotlarni yozing (masalan: tovuq, guruch, pomidor). Men sizga mos sog'lom retsept tuzib beraman:", 
            reply_markup=types.ForceReply(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_recipe_input, bot)
    except Exception as e:
        print(f"Handle Recipe Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_recipe_input(message, bot):
    user_id = message.from_user.id
    if not message.text:
        bot.send_message(message.chat.id, "Iltimos, mahsulotlarni matn ko'rinishida yozing.")
        return
        
    ingredients = message.text
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(message.chat.id, "⏳ <b>Retsept yaratilmoqda...</b>", parse_mode="HTML")
    
    system_prompt = f"""
    Siz professional dietolog va oshpazsiz.
    
    Foydalanuvchi Profili:
    - Maqsad: {user.get('goal')}
    - Faollik: {user.get('activity_level')}
    - Allergiya: {user.get('allergies')}
    
    Vazifa: Foydalanuvchi kiritgan mahsulotlardan foydalanib, uning maqsadiga mos 1 ta sog'lom va mazali retsept taklif qiling.
    
    QAT'IY QOIDALAR (Strict Rules):
    1. Foydalanuvchi yozmagan asosiy mahsulotlarni (go'sht, tuxum, sabzavotlar, sut kabi) o'zingdan qo'shib yozma!
    2. Faqat suv, tuz, yog', murch, shakar kabi eng oddiy "uyda har doim bor" narsalarni bor deb hisobla.
    3. Agar berilgan mahsulotlardan tuzuk ovqat chiqmasa, shuni to'g'ri tushuntir ("Bu mahsulotlardan faqat ... qilish mumkin" yoki "To'yimli taom uchun yana ... kerak").
    4. Xayoliy retsept to'qima. Bor narsadan maksimal foydalan.
    
    FORMAT TALABLARI:
    - Maksimal 1000 belgi.
    - Markdown ishlata ko'rmang (* yoki _).
    - Faqat HTML teglar: <b>, <i>.
    - Struktura:
      * <b>Taom Nomi</b>
      * <b>Masalliqlar</b> (Faqat bor narsalar + suv/yog'/ziravor)
      * <b>Tayyorlash</b> (3-6 qadam)
      * <b>Foydali maslahat</b> (1 gap)
    - O'zbek tilida.
    """
    
    try:
        from core.ai import ask_gemini
        response = ask_gemini(system_prompt, ingredients)
        
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            log_ai_usage(bot, message.from_user.id, "recipe", 300)
        except: pass
        
        try:
            bot.edit_message_text(response, message.chat.id, status_msg.message_id, parse_mode="HTML")
        except Exception:
            bot.edit_message_text(response, message.chat.id, status_msg.message_id, parse_mode=None)
            
        # Send main menu to restore navigation
        from bot.keyboards import main_menu_keyboard
        bot.send_message(user_id, "Yana nima yordam bera olaman?", reply_markup=main_menu_keyboard())
            
    except Exception as e:
        print(f"Recipe Error: {e}")
        bot.edit_message_text("AI hozir retsept tuza olmadi. Mahsulotlar ozroq bo‘lishi yoki tarmoqda muammo bo‘lishi mumkin. Birozdan keyin yana urinib ko‘ring 🙂", message.chat.id, status_msg.message_id)

@require_premium
def handle_weekly_report(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(user_id, "⏳ <b>Haftalik hisobot tayyorlanmoqda...</b>", parse_mode="HTML")
    
    # Fetch real stats
    stats = db.get_weekly_stats(user_id)
    
    if not stats or not stats.get("has_data"):
        bot.edit_message_text(
            "📉 <b>Ma'lumot yetarli emas</b>\n\nTo'liq hisobot olish uchun botdan kamida 2-3 kun faol foydalaning (suv, uyqu, mashg'ulotlarni kiriting).", 
            user_id, 
            status_msg.message_id, 
            parse_mode="HTML"
        )
        return

    # Construct prompt with real data
    prompt = f"""
    Foydalanuvchi: {user.get('full_name')}
    Maqsad: {user.get('goal')}
    
    📊 **So'nggi 7 kunlik statistika:**
    - Faol kunlar: {stats['days_tracked']}/7
    - Suv ichilgan kunlar: {stats['water_days']} (Streak: {stats['streaks']['water']})
    - Mashg'ulotlar: {stats['workouts']} ta
    - O'rtacha uyqu: {stats['avg_sleep']} soat (Streak: {stats['streaks']['sleep']})
    - Kayfiyatlar: {stats['moods']}
    
    Vazifa: Yuqoridagi ma'lumotlarga asoslanib, foydalanuvchiga qisqa, motivatsion haftalik hisobot yozing.
    
    FORMAT:
    📊 **Haftalik Hisobot**
    
    ✅ **Natijalar:**
    - (Aniq raqamlarni keltiring)
    
    💡 **Maslahat:**
    - (Agar uyqu kam bo'lsa yoki suv ichilmagan bo'lsa, shunga urg'u bering)
    
    🔥 **Keyingi hafta uchun:**
    - (Qisqa motivatsiya)
    
    Maksimal 800 belgi. O'zbek tilida.
    """
    
    response = call_gemini(prompt)
    if response:
        # Use format_gemini_text but ensure title isn't duplicated if AI adds it
        formatted = format_gemini_text(response, "Haftalik Hisobot")
        # If format_gemini_text adds a title and AI also adds it, it might be double. 
        # But format_gemini_text usually just ensures bolding. 
        # Let's just send the response if it looks good, or use the formatter.
        # Actually, format_gemini_text is a helper that might add a header. Let's trust it.
        
        try:
            bot.edit_message_text(formatted, user_id, status_msg.message_id, parse_mode="HTML")
        except Exception:
             bot.edit_message_text(formatted, user_id, status_msg.message_id, parse_mode=None)
    else:
        bot.edit_message_text("❌ AI band. Keyinroq urining.", user_id, status_msg.message_id)
