from telebot import types
from core.db import db
from core.utils import generate_referral_code, get_referrer_id_from_code
from bot.keyboards import (
    phone_request_keyboard, gender_keyboard, goal_keyboard, 
    allergy_keyboard, main_menu_keyboard, activity_level_keyboard
)

# States
STATE_NONE = 0
STATE_PHONE = 1
STATE_NAME = 2
STATE_AGE = 3
STATE_GENDER = 4
STATE_HEIGHT = 5
STATE_WEIGHT = 6
STATE_ACTIVITY = 9 # New state
STATE_GOAL = 7
STATE_ALLERGY = 8

class OnboardingManager:
    def __init__(self):
        pass # No local state

    def get_state(self, user_id):
        return db.get_onboarding_state(user_id)

    def set_state(self, user_id, state):
        db.set_onboarding_state(user_id, state)

    def update_data(self, user_id, key, value):
        db.update_onboarding_data(user_id, key, value)

    def get_data(self, user_id):
        return db.get_onboarding_data(user_id)

    def track_message(self, user_id, message_id):
        # Tracking messages can still be in DB or just keep in memory for short term?
        # Ideally DB, but for now let's keep it in DB data
        data = self.get_data(user_id)
        msg_ids = data.get('msg_ids', [])
        if message_id not in msg_ids:
            msg_ids.append(message_id)
            self.update_data(user_id, 'msg_ids', msg_ids)

    def get_messages(self, user_id):
        data = self.get_data(user_id)
        return data.get('msg_ids', [])

    def clear_user(self, user_id):
        db.clear_onboarding_state(user_id)

manager = OnboardingManager()

def start_onboarding(message, bot):
    """Step 0: Check if user exists, if not request phone number FIRST"""
    user_id = message.from_user.id
    
    # Check if user already exists in database
    existing_user = db.get_user(user_id)
    if existing_user:
        bot.send_message(
            user_id, 
            "Asosiy menyuga qaytdingiz, pastdagi tugmalar orqali keyingi qadamni tanlang👇🏻", 
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Handle start parameters
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        code = args[1]
        
        # Handle premium shortcut
        if code == 'premium':
            from bot.premium import handle_premium_menu
            handle_premium_menu(message, bot)
            return
            
        referrer_id = get_referrer_id_from_code(code)
        
        # Prevent self-referral
        if referrer_id == user_id:
            referrer_id = None
    
    # Initialize onboarding
    # Ensure user exists in DB (as partial user) so we can save state
    db.ensure_user_exists(user_id, message.from_user.username)
    
    # --- UTM / Source Tracking ---
    # Logic:
    # 1. If referrer_id found -> Source = 'referral', Campaign = code
    # 2. If no referrer but code exists -> Parse as UTM (e.g. ig_demicstory)
    # 3. If no code -> Source = 'organic'
    
    utm_raw = None
    utm_source = "organic" # Default
    utm_campaign = None
    
    if len(args) > 1:
        code = args[1]
        utm_raw = code
        
        if referrer_id:
            utm_source = "referral"
            utm_campaign = f"user_{referrer_id}"
        elif code != 'premium': # Ignore premium shortcut which is internal
            # Parse custom UTM: source_campaign or just source
            parts = code.split('_', 1)
            if len(parts) == 2:
                utm_source = parts[0]
                utm_campaign = parts[1]
            else:
                utm_source = code 
                # keep campaign None or equal to source? Let's keep None/Generic
    
    db.update_user_utm(user_id, utm_raw, utm_source, utm_campaign)
    # -----------------------------
    
    manager.clear_user(user_id)
    manager.set_state(user_id, STATE_PHONE)
    manager.update_data(user_id, 'referrer_id', referrer_id)
    manager.update_data(user_id, 'msg_ids', []) # Init message tracking
    
    # Track user's start command if possible (message.message_id)
    manager.track_message(user_id, message.message_id)
    
    msg = bot.send_message(
        user_id,
        "🎉 Assalomu alaykum! YASHA botiga xush kelibsiz.\n\n"
        "Davom etish uchun telefon raqamingizni yuboring 👇",
        reply_markup=phone_request_keyboard()
    )
    manager.track_message(user_id, msg.message_id)

def process_phone(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_PHONE:
        return

    if not message.contact:
        bot.send_message(
            user_id,
            "❌ Iltimos, telefon raqamingizni kontakt sifatida yuboring 👇\n\n"
            "Pastdagi tugmani bosing:",
            reply_markup=phone_request_keyboard()
        )
        return
    
    phone = message.contact.phone_number
    manager.update_data(user_id, 'phone', phone)
    manager.set_state(user_id, STATE_NAME)
    
    # Track user message
    manager.track_message(user_id, message.message_id)
    
    msg = bot.send_message(
        user_id, 
        f"✅ Rahmat!\n\n"
        f"Endi ismingizni kiriting:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    manager.track_message(user_id, msg.message_id)

def process_name(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_NAME:
        return
    
    # Validation: Ensure text message
    if not message.text or message.content_type != 'text':
        bot.send_message(user_id, "⚠️ Iltimos, ismingizni matn ko'rinishida yozing (masalan: Ali).")
        return

    name = message.text.strip()
    # Simple prohibited words filter (basic)
    if len(name) > 50 or any(x in name.lower() for x in ['admin', 'bot', 'support']):
         bot.send_message(user_id, "⚠️ Iltimos, haqiqiy ismingizni kiriting.")
         return

    manager.update_data(user_id, 'name', name)
    manager.set_state(user_id, STATE_AGE)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, f"Rahmat, {name}! Yoshingiz nechida? (faqat raqam)")
    manager.track_message(user_id, msg.message_id)

def process_age(message, bot):
    user_id = message.from_user.id
    print(f"DEBUG: process_age called for {user_id}, state: {manager.get_state(user_id)}")
    
    if manager.get_state(user_id) != STATE_AGE:
        try:
             # Clean up old message if button click
             bot.delete_message(message.chat.id, message.message_id) 
        except: pass
        return

    # Check content type FIRST
    if message.content_type != 'text' or not message.text:
        bot.send_message(user_id, "Iltimos, yoshingizni raqamda kiriting (matn):")
        return
        
    if not message.text.isdigit():
        bot.send_message(user_id, "⚠️ Iltimos, yoshingizni faqat raqam bilan yozing (masalan: 25).")
        return
        bot.send_message(user_id, "Iltimos, yoshingizni raqamda kiriting:")
        return
    
    age = int(message.text)
    if age < 10 or age > 120:
        bot.send_message(user_id, "Yoshingizni to'g'ri kiriting (10-120 oralig'ida):")
        return
    
    manager.update_data(user_id, 'age', age)
    manager.set_state(user_id, STATE_GENDER)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, "Jinsingizni tanlang:", reply_markup=gender_keyboard())
    manager.track_message(user_id, msg.message_id)

def process_gender(call, bot):
    user_id = call.from_user.id
    print(f"DEBUG: process_gender called for {user_id}, state: {manager.get_state(user_id)}")
    
    if manager.get_state(user_id) != STATE_GENDER:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    gender = call.data.replace("gender_", "")
    if gender not in ["male", "female"]:
        bot.answer_callback_query(call.id, "❌ Noto'g'ri qiymat.")
        return

    manager.update_data(user_id, 'gender', gender)
    manager.set_state(user_id, STATE_HEIGHT)
    print(f"DEBUG: State updated to STATE_HEIGHT for {user_id}")
    
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"DEBUG: Error answering callback: {e}")
        
    msg = bot.send_message(user_id, "Bo'yingizni kiriting (sm):")
    manager.track_message(user_id, msg.message_id)
    # Explicitly register next step handler as a backup for FSM
    # bot.register_next_step_handler(msg, process_height, bot) 
    # Actually, FSM should handle this via the generic handler in register_handlers
    # But let's make sure the generic handler is catching it.

def process_height(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_HEIGHT:
        return
    
    if message.content_type != 'text' or not message.text:
        bot.send_message(user_id, "Iltimos, bo'yingizni raqamda kiriting (sm):")
        return

    if not message.text.isdigit():
        bot.send_message(user_id, "Iltimos, bo'yingizni raqamda kiriting (sm):")
        return
    
    height = int(message.text)
    if height < 50 or height > 250:
        bot.send_message(user_id, "Bo'yingizni to'g'ri kiriting (50-250 sm):")
        return
    
    manager.update_data(user_id, 'height', height)
    manager.set_state(user_id, STATE_WEIGHT)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, "Vazningizni kiriting (kg):")
    manager.track_message(user_id, msg.message_id)

def process_weight(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_WEIGHT:
        return
    
    try:
        if message.content_type != 'text' or not message.text:
            raise ValueError

        weight = float(message.text)
        if weight < 20 or weight > 300:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, "Vazningizni to'g'ri kiriting (20-300 kg):")
        return
    
    manager.update_data(user_id, 'weight', weight)
    manager.set_state(user_id, STATE_ACTIVITY)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, "Jismoniy faollik darajangizni tanlang:", reply_markup=activity_level_keyboard())
    manager.track_message(user_id, msg.message_id)

def process_activity(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_ACTIVITY:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    activity = call.data.replace("activity_", "")
    manager.update_data(user_id, 'activity_level', activity)
    manager.set_state(user_id, STATE_GOAL)
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
        
    msg = bot.send_message(user_id, "Maqsadingizni tanlang:", reply_markup=goal_keyboard())
    manager.track_message(user_id, msg.message_id)

def process_goal(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_GOAL:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    goal = call.data.replace("goal_", "")
    manager.update_data(user_id, 'goal', goal)
    manager.set_state(user_id, STATE_ALLERGY)
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
        
    msg = bot.send_message(user_id, "Hastaligingiz yoki allergiyangiz mavjudmi?", reply_markup=allergy_keyboard())
    manager.track_message(user_id, msg.message_id)

def process_allergy(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_ALLERGY:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    allergy_choice = call.data
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    
    if allergy_choice == "allergy_yes":
        # Ask for allergy details
        manager.set_state(user_id, STATE_NONE)
        msg = bot.send_message(
            user_id,
            "📝 Qanday hastalik yoki nima mahsulotlarga allergiyangiz bor?\n\n"
            "Masalan: yong'oq, sut, tuxum, gluten, dengiz mahsulotlari",
            reply_markup=types.ReplyKeyboardRemove()
        )
        manager.track_message(user_id, msg.message_id)
        bot.register_next_step_handler(msg, process_allergy_details, bot)
    else:
        # No allergy
        # Send status message
        bot.send_message(user_id, "⏳ Ma'lumotlar saqlanmoqda...")
        
        manager.update_data(user_id, 'allergies', None)
        finish_onboarding(user_id, message=call.message, bot=bot)

def process_allergy_details(message, bot):
    """Process allergy details text input"""
    user_id = message.from_user.id
    
    if not message.text:
        bot.send_message(user_id, "Iltimos, matn yuboring.")
        return

    allergy_details = message.text.strip()
    
    bot.send_message(user_id, "⏳ Ma'lumotlar saqlanmoqda...")
    
    manager.update_data(user_id, 'allergies', allergy_details)
    manager.track_message(user_id, message.message_id)
    
    # Finish Onboarding
    finish_onboarding(user_id, message=message, bot=bot)

def finish_onboarding(user_id, message, bot):
    try:
        print(f"DEBUG: Starting finish_onboarding for {user_id}")
        data = manager.get_data(user_id)
        referrer_id = data.get('referrer_id')
        
        # Prepare profile data
        profile_data = {
            'phone': data.get('phone'),
            'full_name': data.get('name'),
            'age': data.get('age'),
            'gender': data.get('gender'),
            'height': data.get('height'),
            'weight': data.get('weight'),
            'activity_level': data.get('activity_level'),
            'goal': data.get('goal'),
            'allergies': data.get('allergies')
        }
        
        # Execute Transaction
        print(f"DEBUG: Calling complete_onboarding for {user_id}")
        db.complete_onboarding(
            telegram_id=user_id,
            username=message.chat.username or f"user_{user_id}",
            profile_data=profile_data,
            referrer_id=referrer_id
        )
        print(f"DEBUG: complete_onboarding success for {user_id}")
        
        # Handle referral notification
        if referrer_id:
            try:
                ref_user = db.get_user(referrer_id)
                if ref_user:
                    bot.send_message(
                        referrer_id,
                        f"🎉 Yangi do'st ro'yxatdan o'tdi! +1 ball olasiz.\n"
                        f"Jami ballar: {ref_user.get('yasha_points', 0) + 1}"
                    )
            except Exception as e:
                print(f"Referral notify error: {e}")
        
        # Send welcome message - PLAIN TEXT (No HTML) to be safe
        from core.content import content_manager
        welcome_text = content_manager.get(
            "welcome_msg_v2",
            default=(
                "✅ Ro‘yxatdan o‘tdingiz! YASHA ga xush kelibsiz.\n\n"
                "🎁 Sizga 5 kunlik Premium sinov ochildi - hech qanday cheklovsiz barcha AI xizmatlardan foydalanishingiz mumkin.\n\n"
                "Bu 5 kun ichida siz:\n"
                "- shaxsiylashtirilgan mashqlar rejasiga ega bo‘lasiz\n"
                "- o‘zingizga mos ovqatlanish rejasini olasiz\n"
                "- individual retseptlardan foydalanasiz\n"
                "- shaxsiy psixolog va odatlar murabbiyiga ega bo'lasiz\n\n"
                "Bu shunchaki “bot” emas. Bu sog‘lom hayotga kirish uchun birinchi qadam. Agar odatlaringizni o‘zgartirmoqchi bo‘lsangiz, mana shu yerda boshlanadi.\n\n"
                "Quyidagi tugmalar orqali o‘z rejangizni ishga tushiring 👇"
            )
        )
        
        bot.send_message(
            user_id,
            welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode=None # Disabled formatting
        )
        
        # Delete Onboarding Messages - LAST (Background task)
        delete_onboarding_messages(user_id, bot)
        
        # Clear state
        manager.clear_user(user_id)
        print(f"DEBUG: finish_onboarding completed for {user_id}")
        
    except Exception as e:
        print(f"CRITICAL ERROR in finish_onboarding: {e}")
        import traceback
        traceback.print_exc()
        try:
            bot.send_message(user_id, f"⚠️ Tizimda xatolik yuz berdi: {str(e)}")
        except:
            pass
        manager.clear_user(user_id)

def register_handlers(bot):
    """Register all onboarding-related handlers"""
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        start_onboarding(message, bot)
    
    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        process_phone(message, bot)
        
    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_PHONE)
    def handle_phone_fallback(message):
        """Catch non-contact messages during phone step"""
        bot.send_message(
            message.chat.id,
            "❌ Iltimos, telefon raqamingizni kontakt sifatida yuboring 👇\n\n"
            "Pastdagi tugmani bosing:",
            reply_markup=phone_request_keyboard()
        )
        
    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_NAME)
    def handle_name_step(message):
        process_name(message, bot)

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_AGE)
    def handle_age_step(message):
        process_age(message, bot)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
    def handle_gender_step(call):
        try:
            bot.answer_callback_query(call.id)
            process_gender(call, bot)
        except Exception as e:
            print(f"ERROR in handle_gender_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_HEIGHT)
    def handle_height_step(message):
        process_height(message, bot)

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_WEIGHT)
    def handle_weight_step(message):
        process_weight(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('activity_'))
    def handle_activity_step(call):
        try:
            bot.answer_callback_query(call.id)
            process_activity(call, bot)
        except Exception as e:
            print(f"ERROR in handle_activity_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('goal_'))
    def handle_goal_step(call):
        try:
            bot.answer_callback_query(call.id)
            process_goal(call, bot)
        except Exception as e:
            print(f"ERROR in handle_goal_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('allergy_'))
    def handle_allergy_step(call):
        try:
            bot.answer_callback_query(call.id)
            # Call the actual process_allergy function that handles the logic
            process_allergy(call, bot)
        except Exception as e:
            print(f"ERROR in handle_allergy_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass



def delete_onboarding_messages(user_id, bot):
    """Deletes all tracked messages during onboarding"""
    msg_ids = manager.get_messages(user_id)
    if not msg_ids:
        return
        
    for msg_id in msg_ids:
        try:
            bot.delete_message(user_id, msg_id)
        except Exception as e:
            # Message might be too old or already deleted
            # print(f"DEBUG: Failed to delete message {msg_id}: {e}")
            pass
