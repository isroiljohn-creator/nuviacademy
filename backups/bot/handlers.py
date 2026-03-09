from bot import onboarding, gamification, admin, feedback, premium, profile, templates, workout
from bot.keyboards import main_menu_keyboard
from bot import trackers, ai_features, challenges, calorie_scanner

from core.db import db

def register_all_handlers(bot):
    # --- Global Logging Middleware ---
    def log_middleware(bot_instance, update):
        try:
            user_id = None
            content = ""
            type_ = ""
            
            if hasattr(update, 'message') and update.message:
                # CallbackQuery
                user_id = update.from_user.id
                content = f"Callback: {update.data}"
                type_ = "callback"
            elif hasattr(update, 'text'):
                # Message
                user_id = update.from_user.id
                content = update.text
                type_ = "message"
            
            if user_id:
                db.log_activity(user_id, type_, content)
        except Exception as e:
            print(f"Logging Error: {e}")

    # Register middleware manually if supported or use a catch-all check
    # Telebot middleware is a bit specific. Let's use a simple pre-execution hook if possible.
    # Or better, just use a handler that matches everything but doesn't stop propagation?
    # Telebot handlers stop propagation if they handle it.
    # Best way in standard telebot is `bot.register_middleware_handler(log_middleware, update_types=['message', 'callback_query'])`
    try:
        bot.register_middleware_handler(log_middleware, update_types=['message', 'callback_query'])
    except AttributeError:
        # Fallback for older versions or if method missing
        print("Warning: register_middleware_handler not found. Logging might be limited.")
    # --- Admin Handlers (Priority) ---
    admin.register_handlers(bot)

    # --- Calorie Handlers ---
    @bot.message_handler(func=lambda message: message.text == "🍽 Kaloriya tahlili (premium)" or message.text == "🍽 Kaloriya skaneri" or message.text == "🍽 Kaloriya tahlili")
    def calorie_handler(message):
        calorie_scanner.show_calorie_menu(message, bot)

    @bot.message_handler(content_types=['photo'])
    def photo_handler(message):
        # Check for calorie scanner state
        state = onboarding.manager.get_state(message.from_user.id)
        if state == calorie_scanner.STATE_CALORIE_PHOTO:
            calorie_scanner.handle_calorie_photo(message, bot)
            return
        
        # Check for feedback state (if implemented via state, but feedback uses next_step_handler usually)
        # If no state, ignore or handle as generic photo
        pass

    # --- Main Menu Navigation ---
    @bot.message_handler(func=lambda message: message.text == "⬅️ Asosiy menyu")
    def back_to_main(message):
        bot.send_message(message.chat.id, "🏠 Asosiy menyu", reply_markup=main_menu_keyboard())

    @bot.message_handler(func=lambda message: message.text == "⬅️ Premium menyu")
    def back_to_premium(message):
        premium.handle_premium_menu(message, bot)

    # @bot.message_handler(func=lambda message: message.text == "🏋️ Mening Rejam")
    # def menu_plan(message):
    #     workout.handle_plan_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📆 Kunlik odatlar")
    def menu_habits(message):
        trackers.handle_habits_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🤖 AI murabbiy")
    def menu_ai(message):
        ai_features.handle_ai_tools_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔗 Referal")
    def menu_referral(message):
        gamification.handle_referral_link(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔥 Chellenjlar")
    def menu_challenges(message):
        challenges.handle_challenges_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "👤 Profil")
    def menu_profile(message):
        profile.handle_profile(message, bot)

    @bot.message_handler(func=lambda message: message.text in ["💳 Obuna", "💎 Premium"])
    def menu_premium(message):
        premium.handle_premium_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📩 Qayta aloqa")
    def menu_feedback(message):
        feedback.handle_feedback_start(message, bot)

    # --- Sub-Menu Handlers ---

    # Plan
    @bot.message_handler(func=lambda message: message.text == "🤖 AI mashg‘ulot rejasi" or message.text == "🏋️ AI mashq rejasi")
    def plan_workout_ai(message):
        workout.generate_ai_workout(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🥦 AI ovqatlanish rejasi" or message.text == "🥦 AI menyu")
    def plan_meal_ai(message):
        workout.generate_ai_meal(message, bot)

    # Habits
    @bot.message_handler(func=lambda message: message.text == "💧 Suv ichish")
    def habit_water(message):
        trackers.handle_water_tracker(message, bot)

    @bot.message_handler(func=lambda message: message.text == "😴 Uyqu")
    def habit_sleep(message):
        trackers.handle_sleep_tracker(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🙂 Kayfiyat")
    def habit_mood(message):
        trackers.handle_mood_tracker(message, bot)
        
    @bot.message_handler(func=lambda message: message.text == "🚶 Qadamlar")
    def habit_steps(message):
        trackers.handle_steps_tracker(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📊 Odatlar statistikasi")
    def habit_stats(message):
        trackers.handle_habits_stats(message, bot)

    # Habits Input Handlers
    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == trackers.STATE_STEPS_INPUT)
    def steps_input_handler(message):
        trackers.process_steps_input(message, bot)

    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == trackers.STATE_SLEEP_INPUT)
    def sleep_input_handler(message):
        trackers.process_sleep_input(message, bot)

    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == trackers.STATE_MOOD_REASON)
    def mood_reason_handler(message):
        trackers.process_mood_reason(message, bot)
        
    # AI Tools
    @bot.message_handler(func=lambda message: message.text == "❓ AI savol-javob")
    def ai_qa(message):
        ai_features.handle_ai_qa(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🍳 AI retsept")
    def ai_recipe(message):
        ai_features.handle_recipe_gen(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🛒 AI shopping list")
    def ai_shopping(message):
        ai_features.handle_shopping_list(message, bot)

    # Points
    @bot.message_handler(func=lambda message: message.text == "📊 Ballarim")
    def points_my(message):
        gamification.handle_my_points(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🎁 Mukofotlar")
    def points_rewards(message):
        gamification.handle_rewards(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📜 Qoidalar")
    def points_rules(message):
        gamification.handle_rules(message, bot)

    # Challenges
    @bot.message_handler(func=lambda message: message.text == "📆 Haftalik challenge")
    def challenge_weekly(message):
        challenges.handle_weekly_challenge(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🗓 Oylik challenge")
    def challenge_monthly(message):
        challenges.handle_monthly_challenge(message, bot)

    @bot.message_handler(func=lambda message: message.text == "👥 Do‘stlar challenge")
    def challenge_friends(message):
        challenges.handle_friends_challenge(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🏆 Leaderboard")
    def challenge_leaderboard(message):
        challenges.show_leaderboard_message(message, bot)

    # Profile
    @bot.message_handler(func=lambda message: message.text == "✏️ Ma’lumotlarni tahrirlash")
    def profile_edit(message):
        profile.handle_edit_profile_command(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📊 Sog‘liq statistikasi")
    def profile_stats(message):
        profile.handle_profile_stats(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🎯 Maqsadni o‘zgartirish")
    def profile_goal(message):
        profile.handle_change_goal_command(message, bot)

    # Premium
    @bot.message_handler(func=lambda message: message.text == "💳 Premium sotib olish")
    def premium_buy(message):
        premium.handle_premium_buy(message, bot)

    @bot.message_handler(func=lambda message: message.text == "ℹ️ Tariflar")
    def premium_info(message):
        premium.handle_premium_info(message, bot)

    # Register module handlers (callbacks etc)
    onboarding.register_handlers(bot)
    # menu.register_handlers(bot) # Removed
    gamification.register_handlers(bot)
    gamification.register_handlers(bot)
    feedback.register_handlers(bot)
    feedback.register_handlers(bot)
    premium.register_handlers(bot)
    profile.register_handlers(bot)
    templates.register_handlers(bot)
    calorie_scanner.register_handlers(bot)

    # --- Callbacks ---
    
    # Tracker Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('track_'))
    def tracker_action_callback(call):
        type = call.data.split('_')[1]
        if type == 'water': trackers.process_water_callback(call, bot)
        elif type == 'mood': trackers.process_mood_callback(call, bot)
        # Sleep is now input based, but we might have old buttons or need to remove them?
        # The new tracker uses input for sleep, so no callback needed for sleep logic unless we kept buttons.
        # But wait, handle_sleep_tracker in trackers.py now asks for input, so no buttons.
        # So we can remove sleep callback here.
        bot.answer_callback_query(call.id)

    # AI Tool Callbacks (if any left using callbacks)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("ai_tool_"))
    def handle_ai_tool(call):
        from core.utils import parse_callback
        parts = parse_callback(call.data, prefix="ai_tool_", min_parts=3)
        
        if not parts:
            bot.answer_callback_query(call.id, "Xatolik")
            return

        try:
            tool = parts[2]
            
            if tool == "workout":
                # ...
                pass
            elif tool == "diet":
                # ...
                pass
                
            bot.answer_callback_query(call.id, "Tez kunda...")
        except Exception as e:
            print(f"AI tool error: {e}")
            bot.answer_callback_query(call.id, "Xatolik")

    # Challenge Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('challenge_'))
    def challenge_callback(call):
        action = call.data.replace('challenge_', '')
        if action == 'daily': challenges.handle_daily_challenge(call, bot)
        elif action == 'leaderboard': challenges.show_leaderboard(call, bot)
        elif action == 'complete': 
            challenges.complete_challenge(call, bot, 10)
        elif action == 'weekly': challenges.handle_weekly_challenge(call.message, bot)
        elif action == 'monthly': challenges.handle_monthly_challenge(call.message, bot)
        elif action == 'friends': challenges.handle_friends_challenge(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # Calorie Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('calorie_mode_'))
    def calorie_mode_handler(call):
        calorie_scanner.handle_calorie_mode(call, bot)

    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == calorie_scanner.STATE_CALORIE_TEXT)
    def text_calorie_handler(message):
        calorie_scanner.handle_calorie_text(message, bot)

    # --- Inline Menu Callbacks ---

    # Plan Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('plan_'))
    def plan_callback(call):
        action = call.data.replace('plan_', '')
        if action == 'ai_workout': workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
        elif action == 'ai_meal': workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)
        elif action == 'calorie_scan': calorie_scanner.show_calorie_menu(call.message, bot)
        bot.answer_callback_query(call.id)

    # Habits Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('habit_'))
    def habit_callback(call):
        action = call.data.replace('habit_', '')
        if action == 'water': trackers.handle_water_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'sleep': trackers.handle_sleep_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'mood': trackers.handle_mood_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'steps': trackers.handle_steps_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'stats': trackers.handle_habits_stats(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # AI Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('ai_'))
    def ai_callback(call):
        action = call.data.replace('ai_', '')
        # Handle ai_tool_ prefix from old callbacks if any, but we renamed to ai_
        if action == 'qa': ai_features.handle_ai_qa(call.message, bot, user_id=call.from_user.id)
        elif action == 'meal': workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)
        elif action == 'workout': workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
        elif action == 'recipe': ai_features.handle_recipe_gen(call.message, bot, user_id=call.from_user.id)
        elif action == 'shopping': ai_features.handle_shopping_list(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # Points Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('points_'))
    def points_callback(call):
        action = call.data.replace('points_', '')
        if action == 'balance': gamification.handle_my_points(call.message, bot, user_id=call.from_user.id)
        elif action == 'rewards': gamification.handle_rewards(call.message, bot, user_id=call.from_user.id)
        elif action == 'rules': gamification.handle_rules(call.message, bot)
        elif action == 'referral': gamification.handle_referral_link(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # Challenges Callbacks (Merged with existing if needed, but existing uses challenge_ prefix too)
    # Existing handler handles: daily, leaderboard, complete.
    # We added: weekly, monthly, friends, leaderboard.
    # Let's update the existing handler or add new logic.
    # Existing handler is at line 192. I will replace it or merge.
    # I'll replace the existing challenge callback handler to include new menu items.

    # Profile Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('profile_'))
    def profile_callback(call):
        action = call.data.replace('profile_', '')
        if action == 'edit': profile.handle_edit_profile_command(call.message, bot)
        elif action == 'stats': profile.handle_profile_stats(call.message, bot, user_id=call.from_user.id)
        elif action == 'change_goal': profile.handle_change_goal_command(call.message, bot)
        bot.answer_callback_query(call.id)

    # Premium Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('premium_'))
    def premium_callback(call):
        action = call.data.replace('premium_', '')
        if action == 'buy': premium.handle_premium_buy(call.message, bot)
        elif action == 'info': premium.handle_premium_info_detailed(call.message, bot)
        elif action == 'coins': gamification.handle_points_menu(call.message, bot, user_id=call.from_user.id)
        elif action == 'offer': premium.handle_offer_download(call.message, bot)
        bot.answer_callback_query(call.id)

    # General utility handlers
    @bot.message_handler(commands=['menu'])
    def handle_menu_command(message):
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_keyboard())

    @bot.message_handler(commands=['ping'])
    def handle_ping(message):
        bot.reply_to(message, "Pong! 🏓 Bot ishlamoqda.")

    @bot.message_handler(commands=['myid'])
    def handle_myid(message):
        bot.reply_to(message, f"🆔 Sizning ID raqamingiz: `{message.from_user.id}`", parse_mode="Markdown")

    @bot.message_handler(commands=['reset'])
    def handle_reset(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        onboarding.manager.clear_user(user_id)
        try:
            bot.clear_step_handler_by_chat_id(chat_id)
        except Exception as e:
            print(f"Error clearing step handler: {e}")
        bot.reply_to(message, "🔄 Holat to'liq tozalandi. /start ni bosing.")

    @bot.message_handler(commands=['version'])
    def handle_version(message):
        bot.reply_to(message, "🤖 Bot Version: v3.1 - FIXES APPLIED (Dec 3)")

    @bot.message_handler(commands=['debug_ai'])
    def handle_debug_ai(message):
        from core.config import ADMIN_IDS
        if message.from_user.id not in ADMIN_IDS:
            return

        import google.generativeai as genai
        import os
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            bot.reply_to(message, "❌ API Key topilmadi!")
            return
        
        bot.reply_to(message, f"🔄 Model: gemini-2.5-flash sinalyapti...")
        
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content("Test")
            bot.reply_to(message, f"✅ Success! Response: {response.text}")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    # [DUPLICATE HANDLER REMOVED]
    # The clean implementation is below at line 514+

    @bot.callback_query_handler(func=lambda call: call.data == "menu_shopping")
    def callback_menu_shopping(call):
        try:
            link = db.get_user_menu_link(call.from_user.id)
            if not link:
                bot.answer_callback_query(call.id, "Reja topilmadi.")
                return

            import json
            shopping_list = json.loads(link['shopping_list_json'])
            
            if not shopping_list:
                bot.answer_callback_query(call.id, "Shopping list bo'sh.")
                return
              # Debugging: Show internal state
            menu = json.loads(link['menu_json'])
            total_days = len(menu)
            day2_preview = "Yo'q"
            if total_days >= 2:
                day2_preview = menu[1].get('breakfast', 'N/A')
                
            debug_msg = (
                f"🛠 DEBUG SERVER:\n"
                f"Jami kunlar: {total_days}\n"
                f"Joriy kun (DB): {link['current_day_index']}\n"
                f"2-kun bor? {day2_preview}\n"
            )
            
            # shopping list text logic...
            s_list = json.loads(link['shopping_list_json'])
            txt = f"{debug_msg}\n🛒 **Xaridlar ro'yxati:**\n\n"
            for item in s_list:
                txt += f"▫️ {item}\n"
                
            bot.send_message(call.from_user.id, txt, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"Shopping List Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")




    @bot.callback_query_handler(func=lambda call: call.data.startswith("menu_next_") or call.data.startswith("menu_prev_"))
    def callback_menu_nav(call):
        """ULTRA-SIMPLE navigation - just show the next/prev day."""
        try:
            # Extract day number from callback
            parts = call.data.split("_")  # ["menu", "next/prev", "day_number"]
            # Fix: Safe parsing
            if len(parts) < 3:
                bot.answer_callback_query(call.id, "Xatolik: Ma'lumot yetarli emas")
                return
            
            current_day = int(parts[2])
            
            # Calculate new day
            if "next" in call.data:
                new_day = current_day + 1
            else:
                new_day = current_day - 1
            
            # Clamp to valid range
            if new_day < 1:
                new_day = 1
            
            # Get menu data
            link = db.get_user_menu_link(call.from_user.id)
            if not link:
                bot.answer_callback_query(call.id, "Menyu topilmadi!")
                return
            
            # Delete old message
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            
            # Show new day
            workout.show_daily_menu(bot, call.from_user.id, link, override_day_idx=new_day)
            
        except Exception as e:
            error_msg = f"Xatolik: {str(e)[:50]}"
            print(f"Navigation Error: {e}")
            bot.answer_callback_query(call.id, error_msg)
            bot.send_message(call.from_user.id, f"❌ {error_msg}")

    # =========================================================
    # WORKOUT NAVIGATION (Mirrors Menu Navigation)
    # =========================================================

    @bot.callback_query_handler(func=lambda call: call.data == "workout_regenerate")
    def callback_workout_regenerate(call):
        """Regenerate workout plan logic."""
        try:
             # Deactivate active link
            db.deactivate_all_user_workouts(call.from_user.id)
            
            # Delete message and restart generation
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            
            # Trigger fresh generation
            workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
            bot.answer_callback_query(call.id, "✅ Jarayon boshlandi...")
            
        except Exception as e:
            print(f"Workout Regen Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("workout_next_") or call.data.startswith("workout_prev_"))
    def callback_workout_nav(call):
        """Workout navigation - just show the next/prev day."""
        try:
            # Extract day number
            parts = call.data.split("_")  # ["workout", "next/prev", "day_number"]
            current_day = int(parts[2])
            
            # Calculate new day
            if "next" in call.data:
                new_day = current_day + 1
            else:
                new_day = current_day - 1
            
            # Clamp to valid range (1-7)
            if new_day < 1:
                new_day = 1
            # Note: Max cap is handled in show_daily_workout via JSON length
            
            # Get data
            link = db.get_user_workout_link(call.from_user.id)
            if not link:
                bot.answer_callback_query(call.id, "Reja topilmadi.")
                return
            
            # Delete old message
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            
            # Show new day
            workout.show_daily_workout(bot, call.from_user.id, link, override_day_idx=new_day)
            
        except Exception as e:
            print(f"Workout Nav Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    @bot.callback_query_handler(func=lambda call: call.data == "menu_shopping")
    def callback_menu_shopping(call):
        try:
            link = db.get_user_menu_link(call.from_user.id)
            if not link:
                bot.answer_callback_query(call.id, "Reja topilmadi.")
                return

            import json
            shopping_list = json.loads(link['shopping_list_json'])
            
            if not shopping_list:
                bot.answer_callback_query(call.id, "Shopping list bo'sh.")
                return
                
            txt = "🛒 **30 KUNLIK XARIDLAR RO'YXATI**\n\n"
            for item in shopping_list:
                txt += f"▫️ {item}\n"
                
            bot.send_message(call.from_user.id, txt, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"Shopping List Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    @bot.callback_query_handler(func=lambda call: call.data == "menu_regenerate")
    def callback_menu_regenerate(call):
        try:
            bot.answer_callback_query(call.id, "✅ Jarayon boshlandi...")
            
            # Deactivate active link so generate_ai_meal sees clean state
            db.deactivate_all_user_menus(call.from_user.id)
            
            # Delete message and restart generation
            bot.delete_message(call.message.chat.id, call.message.message_id)
            
            # Trigger fresh generation
            workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)

        except Exception as e:
            print(f"Regen Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    # --- FALLBACK HANDLER (MUST BE LAST) ---
    @bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact'], func=lambda m: True)
    def fallback_handler(message):
        """
        Catches any unhandled message when user is NOT in a specific state.
        Redirects to Main Menu without crashing or resetting state.
        """
        user_id = message.from_user.id
        current_state = onboarding.manager.get_state(user_id)
        
        if current_state != onboarding.STATE_NONE:
            return

        try:
            bot.send_message(
                message.chat.id,
                "🤷‍♂️ Uzr, men bu xabarni tushunmadim.\n\n"
                "Iltimos, pastdagi menyudan kerakli bo‘limni tanlang 👇",
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            print(f"Fallback error: {e}")
