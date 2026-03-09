from telebot import types
from telebot.apihelper import ApiTelegramException
from core.db import db
from core.utils import generate_referral_code, get_referrer_id_from_code
from bot.keyboards import (
    phone_request_keyboard, gender_keyboard, goal_keyboard, 
    allergy_keyboard, main_menu_keyboard, activity_level_keyboard,
    language_selection_keyboard, onboarding_welcome_keyboard
)
from bot.languages import get_text

from core.config import ADMIN_IDS

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
STATE_LANG = 10

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
    """Step 0: Start onboarding with language selection"""
    user_id = message.from_user.id
    
    # Check if user already exists AND has completed onboarding
    existing_user = db.get_user(user_id)
    if existing_user and existing_user.get('is_onboarded'):
        lang = existing_user.get('language', 'uz')
        bot.send_message(
            user_id, 
            get_text("onboarding_back_home", lang=lang, default="Asosiy menyuga qaytdingiz!"),
            reply_markup=main_menu_keyboard(user_id=user_id, lang=lang)
        )
        return
    
    # Initialize onboarding
    db.ensure_user_exists(user_id, message.from_user.username)
    manager.clear_user(user_id)
    manager.set_state(user_id, STATE_LANG)
    
    msg = bot.send_message(
        user_id,
        "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:",
        reply_markup=language_selection_keyboard()
    )
    manager.track_message(user_id, msg.message_id)

def ask_language(message, bot):
    """Explicitly ask for language change (Re-entry)"""
    user_id = message.from_user.id
    manager.set_state(user_id, STATE_LANG)
    
    msg = bot.send_message(
        user_id,
        "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:",
        reply_markup=language_selection_keyboard()
    )
    manager.track_message(user_id, msg.message_id)

def process_language(call, bot):
    """Process language selection"""
    user_id = call.from_user.id
    lang_code = call.data.replace("lang_", "")
    
    db.set_user_language(user_id, lang_code)
    manager.update_data(user_id, 'language', lang_code)
    user_data = db.get_user(user_id)
    is_registered = user_data and user_data.get('is_onboarded')
    
    bot.answer_callback_query(call.id, get_text("language_selected", lang=lang_code))
    
    if is_registered:
        # Already registered? Just update lang and show main menu
        msg_text = get_text("language_change_success", lang=lang_code)
        
        bot.send_message(
            user_id,
            msg_text,
            reply_markup=main_menu_keyboard(user_id=user_id, lang=lang_code)
        )
        # Clear state just in case
        manager.clear_user(user_id)
    else:
        # New user? Continue onboarding
        manager.set_state(user_id, STATE_PHONE)
        msg = bot.send_message(
            user_id,
            get_text("welcome", lang=lang_code, name=call.from_user.first_name) + "\n\n" +
            get_text("request_phone", lang=lang_code, default="Davom etish uchun telefon raqamingizni yuboring 👇"),
            reply_markup=phone_request_keyboard(lang=lang_code)
        )
        manager.track_message(user_id, msg.message_id)

def process_phone(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_PHONE:
        return

    lang = manager.get_data(user_id).get('language', 'uz')
    
    if not message.contact:
        bot.send_message(
            user_id,
            get_text("request_phone", lang=lang, default="Iltimos, telefon raqamingizni kontakt sifatida yuboring 👇"),
            reply_markup=phone_request_keyboard(lang=lang)
        )
        return
    
    phone = message.contact.phone_number
    manager.update_data(user_id, 'phone', phone)
    manager.set_state(user_id, STATE_NAME)
    
    # Track user message
    manager.track_message(user_id, message.message_id)
    
    msg = bot.send_message(
        user_id, 
        f"✅\n\n" + get_text("enter_name", lang=lang),
        reply_markup=types.ReplyKeyboardRemove()
    )
    manager.track_message(user_id, msg.message_id)

def process_name(message, bot):
    user_id = message.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_NAME:
        return
    
    # Validation: Ensure text message
    if not message.text or message.content_type != 'text':
        bot.send_message(user_id, get_text("error_generic", lang=lang))
        return

    name = message.text.strip()
    # Simple prohibited words filter (basic)
    if len(name) > 50 or any(x in name.lower() for x in ['admin', 'bot', 'support']):
         bot.send_message(user_id, get_text("error_name_invalid", lang=lang))
         return

    manager.update_data(user_id, 'name', name)
    manager.set_state(user_id, STATE_AGE)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("onboarding_age", lang=lang, name=name))
    manager.track_message(user_id, msg.message_id)

def process_age(message, bot):
    user_id = message.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_AGE:
        try:
             bot.delete_message(message.chat.id, message.message_id) 
        except: pass
        return

    # Check content type FIRST
    if message.content_type != 'text' or not message.text:
        bot.send_message(user_id, get_text("error_age_number", lang=lang))
        return
        
    if not message.text.isdigit():
        bot.send_message(user_id, get_text("error_age_invalid", lang=lang))
        return
    
    age = int(message.text)
    if age < 10 or age > 120:
        bot.send_message(user_id, get_text("error_age_range", lang=lang))
        return
    
    manager.update_data(user_id, 'age', age)
    manager.set_state(user_id, STATE_GENDER)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("onboarding_gender", lang=lang), reply_markup=gender_keyboard(lang=lang))
    manager.track_message(user_id, msg.message_id)

def process_gender(call, bot):
    user_id = call.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_GENDER:
        try:
            bot.answer_callback_query(call.id, "...")
        except:
            pass
        return
    
    gender = call.data.replace("gender_", "")
    if gender not in ["male", "female"]:
        bot.answer_callback_query(call.id, "❌")
        return

    manager.update_data(user_id, 'gender', gender)
    manager.set_state(user_id, STATE_HEIGHT)
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
        
    msg = bot.send_message(user_id, get_text("onboarding_height", lang=lang))
    manager.track_message(user_id, msg.message_id)

def process_height(message, bot):
    user_id = message.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_HEIGHT:
        return
    
    if message.content_type != 'text' or not message.text:
        bot.send_message(user_id, get_text("error_age_number", lang=lang))
        return

    if not message.text.isdigit():
        bot.send_message(user_id, get_text("error_age_number", lang=lang))
        return
    
    height = int(message.text)
    if height < 50 or height > 250:
        bot.send_message(user_id, get_text("onboarding_height", lang=lang))
        return
    
    manager.update_data(user_id, 'height', height)
    manager.set_state(user_id, STATE_WEIGHT)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("onboarding_weight", lang=lang))
    manager.track_message(user_id, msg.message_id)

def process_weight(message, bot):
    user_id = message.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_WEIGHT:
        return
    
    try:
        if message.content_type != 'text' or not message.text:
            raise ValueError

        weight = float(message.text)
        if weight < 20 or weight > 300:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, get_text("onboarding_weight", lang=lang))
        return
    
    manager.update_data(user_id, 'weight', weight)
    manager.set_state(user_id, STATE_ACTIVITY)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("onboarding_activity", lang=lang), reply_markup=activity_level_keyboard(lang=lang))
    manager.track_message(user_id, msg.message_id)

def process_activity(call, bot):
    user_id = call.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_ACTIVITY:
        try:
            bot.answer_callback_query(call.id, "...")
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
        
    msg = bot.send_message(user_id, get_text("onboarding_goal", lang=lang), reply_markup=goal_keyboard(lang=lang))
    manager.track_message(user_id, msg.message_id)

def process_goal(call, bot):
    user_id = call.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_GOAL:
        try:
            bot.answer_callback_query(call.id, "...")
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
        
    msg = bot.send_message(user_id, get_text("onboarding_allergy_question", lang=lang), reply_markup=allergy_keyboard(lang=lang))
    manager.track_message(user_id, msg.message_id)

def process_allergy(call, bot):
    user_id = call.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if manager.get_state(user_id) != STATE_ALLERGY:
        try:
            bot.answer_callback_query(call.id, "...")
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
            get_text("onboarding_allergy_details", lang=lang),
            reply_markup=types.ReplyKeyboardRemove()
        )
        manager.track_message(user_id, msg.message_id)
        bot.register_next_step_handler(msg, process_allergy_details, bot)
    else:
        # No allergy
        # Send status message
        bot.send_message(user_id, get_text("onboarding_saving", lang=lang))
        
        manager.update_data(user_id, 'allergies', None)
        finish_onboarding(user_id, message=call.message, bot=bot)

def process_allergy_details(message, bot):
    """Process allergy details text input"""
    user_id = message.from_user.id
    lang = manager.get_data(user_id).get('language', 'uz')
    
    if not message.text:
        bot.send_message(user_id, get_text("error_generic", lang=lang))
        return

    allergy_details = message.text.strip()
    
    if len(allergy_details) > 200:
        bot.send_message(user_id, get_text("error_generic", lang=lang)) # TODO: Add more specific errors
        return
    
    bot.send_message(user_id, get_text("onboarding_saving", lang=lang))
    
    manager.update_data(user_id, 'allergies', allergy_details)
    manager.track_message(user_id, message.message_id)
    
    # Finish Onboarding
    finish_onboarding(user_id, message=message, bot=bot)

def finish_onboarding(user_id, message, bot):
    try:
        data = manager.get_data(user_id)
        lang = data.get('language', 'uz')
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
            'allergies': data.get('allergies'),
            'language': lang
        }
        
        # Execute Transaction
        db.complete_onboarding(
            telegram_id=user_id,
            username=message.chat.username or f"user_{user_id}",
            profile_data=profile_data,
            referrer_id=referrer_id
        )
        
        # Log Event [NEW]
        db.log_event(user_id, "onboarding_completed")

        
        # Handle referral notification
        if referrer_id:
            try:
                ref_user = db.get_user(referrer_id)
                if ref_user:
                    ref_lang = ref_user.get('language', 'uz')
                    points_total = ref_user.get('yasha_points', 0) + 1
                    ref_msg = get_text("referral_friend_joined", lang=ref_lang, points=points_total)
                    bot.send_message(referrer_id, ref_msg)
            except Exception as e:
                print(f"Referral notify error: {e}")
        
        # ACTIVATE TRIAL
        try:
            db.activate_trial(user_id, days=7)
        except Exception as e:
            print(f"Trial Activation Error: {e}")

        # Send welcome message
        welcome_text = get_text("onboarding_welcome_trial", lang=lang)
        
        bot.send_message(
            user_id,
            welcome_text,
            reply_markup=onboarding_welcome_keyboard(lang=lang),
            parse_mode="Markdown"
        )
        
        # Also ensure they have the main menu reply keyboard separately or send a small message
        bot.send_message(
            user_id,
            get_text("onboarding_back_home", lang=lang),
            reply_markup=main_menu_keyboard(user_id=user_id, lang=lang)
        )
        
        # Delete Onboarding Messages
        delete_onboarding_messages(user_id, bot)
        
        # Clear state
        manager.clear_user(user_id)
        
    except Exception as e:
        print(f"CRITICAL ERROR in finish_onboarding: {e}")
        import traceback
        traceback.print_exc()
        try:
            # Fallback to ALLERGY state to allow retry
            manager.set_state(user_id, STATE_ALLERGY)
            
            # Send friendly error message
            err_msg = get_text("error_generic", lang, default="Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")
            if str(e): # Append technical error if available (optional, maybe too technical?)
                 # Keep it simple for user, log for admin.
                 pass
                 
            bot.send_message(
                user_id, 
                f"⚠️ {err_msg}",
                reply_markup=allergy_keyboard(lang)
            )
        except Exception as inner_e:
            print(f"Recovery failed: {inner_e}")
            # If recovery fails, THEN clear
            manager.clear_user(user_id)

def register_handlers(bot):
    """Register all onboarding-related handlers"""
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        start_onboarding(message, bot)
    
    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        process_phone(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
    def handle_language_step(call):
        process_language(call, bot)
        
    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_PHONE)
    def handle_phone_fallback(message):
        """Catch non-contact messages during phone step"""
        user_id = message.from_user.id
        lang = db.get_user_language(user_id)
        try:
            bot.send_message(
                message.chat.id,
                get_text("request_phone", lang=lang, default="Iltimos, telefon raqamingizni kontakt sifatida yuboring 👇"),
                reply_markup=phone_request_keyboard(lang=lang)
            )
        except ApiTelegramException as e:
            if e.error_code == 403:
                print(f"User {message.chat.id} blocked the bot (phone_fallback).")
            else:
                raise e
        
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
    @bot.callback_query_handler(func=lambda call: call.data == 'show_public_offer')
    def handle_public_offer(call):
        try:
            user_id = call.from_user.id
            lang = db.get_user_language(user_id)
            offer_text = get_text("public_offer_text", lang=lang)
            
            # Show offer text as a new message or edit current? 
            # Better as a new message to keep the welcome message visible
            bot.send_message(user_id, offer_text)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Error showing public offer: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except: pass





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
