from telebot import types
from core.ai import call_gemini, format_gemini_text
from core.db import db
from bot.premium import require_premium
from bot.languages import get_text

from bot.keyboards import ai_inline_keyboard

def handle_ai_tools_menu(message, bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    caption = get_text("ai_coach_caption", lang)
    
    with open("assets/ai_murabbiy.png", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption=caption,
            reply_markup=ai_inline_keyboard(lang=lang),
            parse_mode="HTML"
        )

@require_premium
def handle_ai_qa(message, bot, user_id=None):
    if user_id is None: user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    from bot.languages import get_text
    try:
        msg_text = get_text("ai_qa_prompt", lang=lang)
        msg = bot.send_message(
            message.chat.id, 
            msg_text, 
            reply_markup=types.ForceReply(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_ai_qa, bot)
    except Exception as e:
        print(f"Handle AI QA Error: {e}")
        error_text = get_text("error_generic", lang=lang)
        bot.send_message(message.chat.id, error_text)

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
    - O'zbek tilida (Lotin alifbosi).
    """
    if user.get('language') == 'ru':
        system_prompt = f"""
    You are a professional fitness coach.
    
    User Profile:
    - Age: {user.get('age')}
    - Gender: {user.get('gender')}
    - Height: {user.get('height')} cm
    - Weight: {user.get('weight')} kg
    - Goal: {user.get('goal')}
    - Activity: {user.get('activity_level')}
    
    Task: Answer the question clearly and accurately, tailored to the user profile.
    
    FORMAT RULES:
    - Max 700-900 chars.
    - Short paragraphs.
    - Use <b>bold</b> (HTML) for keywords.
    - Use bullets (-) for lists.
    - NO Markdown (* or _).
    - ONLY HTML tags: <b>, <i>, <u>, <s>, <code>, <pre>.
    - Respond strictly in RUSSIAN.
    """
    
    # Check Limit
    from core.entitlements import check_and_consume
    ent = check_and_consume(user_id, 'ai_chat')
    if not ent['allowed']:
        bot.send_message(user_id, ent['message_uz'], parse_mode="Markdown")
        return

    try:
        # 1. Check QA Database (Fast Local Match)
        from core.qa_engine import get_best_match
        
        db_match = get_best_match(question, threshold=0.60)
        
        response = None
        if db_match:
            response = db_match['match']['answer']
            # Log event for internal tracking
            db.log_event(user_id, "ai_chat_db_hit")
        else:
            # 2. Fallback to Gemini AI
            from core.ai import ask_gemini
            response = ask_gemini(system_prompt, question)
            
            # Log Event [NEW]
            db.log_event(user_id, "ai_chat_used")


        
        from bot.languages import get_text
        lang = user.get('language', 'uz')
        
        # Edit status message with response
        try:
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode="HTML")
        except Exception:
            # Fallback to plain text if HTML is invalid
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode=None)
            
        # Send main menu to restore navigation
        from bot.keyboards import main_menu_keyboard
        back_msg = get_text("ai_qa_back", lang=lang)
        bot.send_message(user_id, back_msg, reply_markup=main_menu_keyboard(user_id=user_id, lang=lang))
            
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
        lang = db.get_user_language(user_id)
        
        if not shopping_list:
            bot.send_message(user_id, get_text("shopping_list_empty", lang), parse_mode="HTML")
            return
            
        # Log Event [NEW]
        db.log_event(user_id, "shopping_list_opened")

            
        # 3. Format and Send
        title = get_text("shopping_list_title_30", lang)
        sub = get_text("shopping_list_sub", lang)
        
        txt = f"{title}\n\n"
        txt += f"{sub}\n\n"
        
        for item in shopping_list:
            txt += f"▫️ {item}\n"
            
        bot.send_message(user_id, txt, parse_mode="HTML")
        
    except Exception as e:
        print(f"Shopping List Error: {e}")
        bot.send_message(user_id, get_text("error_generic", lang))

@require_premium
def handle_recipe_gen(message, bot, user_id=None):
    if user_id is None: user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    msg_text = get_text("ai_recipe_prompt", lang=lang)
    try:
        msg = bot.send_message(
            message.chat.id, 
            msg_text, 
            reply_markup=types.ForceReply(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_recipe_input, bot)
    except Exception as e:
        print(f"Handle Recipe Error: {e}")
        bot.send_message(message.chat.id, "❌ Error")

def process_recipe_input(message, bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    if not message.text:
        bot.send_message(message.chat.id, get_text("error_text_only", lang=lang))
        return
        
    ingredients = message.text
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(message.chat.id, "⏳ <b>Retsept yaratilmoqda...</b>", parse_mode="HTML")
    
    system_prompt = f"""
    Siz professional diyetolog va oshpazsiz.
    
    Foydalanuvchi Profili:
    - Maqsad: {user.get('goal')}
    - Faollik: {user.get('activity_level')}
    - Allergiya: {user.get('allergies')}
    
    Vazifa: Berilgan masalliqlardan foydalanib, foydalanuvchi maqsadiga mos 1 ta sog'lom retsept taklif qiling.
    
    FORMAT TALABLARI:
    - Retsept nomi (Qalin harflarda)
    - Teyyorlash vaqti va Kaloriyasi
    - Kerakli masalliqlar ro'yxati
    - Tayyorlash bosqichlari (qadamma-qadam)
    - Foydali tomonlari
    - O'zbek tilida (Lotin alifbosi).
    """
    if user.get('language') == 'ru':
        system_prompt = f"""
    You are a professional nutritionist and chef.
    
    User Profile:
    - Goal: {user.get('goal')}
    - Activity: {user.get('activity_level')}
    - Allergy: {user.get('allergies')}
    
    Task: Suggest 1 healthy recipe based on ingredients provided.
    
    STRICT RULES:
    1. DO NOT invent main ingredients not mentioned.
    2. Only assume basic staples like water, salt, oil, pepper.
    3. If no good meal can be made, explain why.
    4. Don't make up fantasy recipes.
    
    FORMAT:
    - Max 1000 chars.
    - NO Markdown. Use HTML.
    - Structure:
      * <b>Recipe Name</b>
      * <b>Ingredients</b>
      * <b>Preparation</b> (3-6 steps)
      * <b>Tip</b> (1 sentence)
    - Respond strictly in RUSSIAN.
    """
    
    # Check Limit
    from core.entitlements import check_and_consume
    ent = check_and_consume(user_id, 'explain_engine') # Using explain_engine limit for recipes as close proxy? 
    # Or create new key? Matrix doesn't specify recipe limit explicitly. 
    # It might be under 'ai_chat' or 'menu_generate'.
    # Let's use 'menu_generate' NO, that's monthly.
    # 'ai_chat' is daily 5. Recipes are similar.
    # Let's use 'ai_chat' for recipe gen too for now to be safe.
    ent = check_and_consume(user_id, 'ai_chat') 
    
    if not ent['allowed']:
         time = "Bugun" if ent['period'] == 'day' else "Bu oy"
         bot.send_message(message.chat.id, ent['message_uz'], parse_mode="Markdown")
         return
    
    try:
        from core.ai import ask_gemini
        response = ask_gemini(system_prompt, ingredients)
        
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            log_ai_usage(bot, message.from_user.id, "recipe", 300)
        except: pass
        
        # Log Event [NEW]
        db.log_event(user_id, "recipe_generated")

        
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
    
    # Check Limit
    from core.entitlements import check_and_consume
    ent = check_and_consume(user_id, 'weekly_mirror')
    if not ent['allowed']:
         bot.edit_message_text(ent['message_uz'], user_id, status_msg.message_id, parse_mode="Markdown")
         return

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
    lang_instruction = "Javob O'zbek tilida."
    if user.get('language') == 'ru':
        lang_instruction = "Respond strictly in Russian."

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
    📊 **Haftalik Hisobot** (Translate title if needed)
    
    ✅ **Natijalar:**
    - (Aniq raqamlarni keltiring)
    
    💡 **Maslahat:**
    - (Agar uyqu kam bo'lsa yoki suv ichilmagan bo'lsa, shunga urg'u bering)
    
    🔥 **Keyingi hafta uchun:**
    - (Qisqa motivatsiya)
    
    Maksimal 800 belgi. {lang_instruction}
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
