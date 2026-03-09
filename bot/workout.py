import os
from telebot import types
from core.db import db
from core.ai import ai_generate_weekly_workout_json, ai_generate_weekly_meal_plan_json
from core.nutrition import process_menu_nutrition
from bot.keyboards import plan_inline_keyboard
from bot.premium import require_premium
from bot.languages import get_text
from core.flags import is_flag_enabled
import traceback

import threading
from core.ymove import parse_and_find_videos
# Thread-safe in-memory lock
GENERATION_LOCKS = set()
LOCKS_MUTEX = threading.Lock()

from core.entitlements import get_user_plan


def handle_plan_menu(message, bot):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    bot.send_message(
        message.chat.id,
        f"🏋️ **{get_text('menu_plan', lang)}**\n\n{get_text('choose_plan_type', lang)}",
        reply_markup=plan_inline_keyboard(lang=lang),
        parse_mode="Markdown"
    )

def handle_workout_plan(message, bot):
    """Entry point for workout plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_workout_template_menu
    show_workout_template_menu(message, bot)

def handle_meal_plan(message, bot):
    """Entry point for meal plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_meal_template_menu
    show_meal_template_menu(message, bot)

def generate_ai_workout(message, bot, user_id=None):
    """Generate AI workout plan (7-Day JSON System)"""
    from core.ai import ai_generate_weekly_workout_json, get_free_workout_template
    import json
    import time
    
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    # 0. Check Plan
    is_premium = db.is_premium(user_id)
    lang = user.get('language', 'uz')
    
    if not is_premium:
        # FREE TIER LOGIC
        data = get_free_workout_template(user, lang=lang)
        
        # Save Template
        # Key: free_workout_Goal
        profile_key = f"free_workout_{user.get('goal')}".replace(" ", "_").lower()
        
        try:
             import json
             template_id = db.create_workout_template(profile_key, json.dumps(data['schedule']))
        except:
             # Fallback if exists
             exist = db.get_workout_template(profile_key)
             template_id = exist['id'] if exist else None
             
             template_id = exist['id'] if exist else None
             
        if template_id:
             db.create_user_workout_link(user_id, template_id)
             
             # LOCALIZED
             lang = user.get('language', 'uz')
             bot.send_message(user_id, get_text("free_workout_ready", lang))
             
             # Log Event [NEW]
             db.log_event(user_id, "workout_generated", {"type": "template", "tier": "free"})

             
             # Enhanced Plus Teaser
             markup = types.InlineKeyboardMarkup()
             markup.add(types.InlineKeyboardButton(get_text("btn_get_plus", lang), callback_data="premium_info"))
             
             upsell_msg = get_text("upsell_workout_plus", lang)
             bot.send_message(user_id, upsell_msg, parse_mode="Markdown", reply_markup=markup)
             
             new_link = db.get_user_workout_link(user_id)
             show_daily_workout(bot, user_id, new_link, override_day_idx=1)
        else:
             lang = user.get('language', 'uz')
             bot.send_message(user_id, get_text("error_template", lang))
        return

    # 0. Check Limit (Premium Only)
    allowed, limit_msg = db.check_ai_gen_limit(user_id, 'workout')
    if not allowed:
        bot.send_message(user_id, limit_msg, parse_mode="Markdown")
        return

    # 0.5 Check Lock
    with LOCKS_MUTEX:
        if user_id in GENERATION_LOCKS:
            bot.send_message(user_id, "⏳ Sabr qiling, reja tuzilmoqda...")
            return
        GENERATION_LOCKS.add(user_id)
        
    try:
        # 1. Check if user already has an active workout link
        active_link = db.get_user_workout_link(user_id)
        if active_link:
            # Auto-open today's workout
            show_daily_workout(bot, user_id, active_link)
            return

        # 2. Build Shared Profile Key (Deduplication)
        # Group users by simple age bands to increase matches
        age = user.get('age', 25)
        age_band = "18-25"
        if age > 45: age_band = "46+"
        elif age > 35: age_band = "36-45"
        elif age > 25: age_band = "26-35"
        
        # Key: workout_v2_Gender_Goal_Activity_AgeBand
        profile_key = f"workout_v2_{user.get('gender')}_{user.get('goal')}_{user.get('activity_level')}_{age_band}".replace(" ", "_").lower()

        # 3. Check for Existing Shared Template
        existing_template = db.get_workout_template(profile_key)
        
        if existing_template:
            bot.send_message(user_id, get_text("found_existing_plan", lang))
            db.create_user_workout_link(user_id, existing_template['id'])
            
            new_link = db.get_user_workout_link(user_id)
            db.increment_ai_usage(user_id, 'workout') 
            show_daily_workout(bot, user_id, new_link, override_day_idx=1)
            return

        # If no template, generate new
        msg = bot.send_message(user_id, get_text("wait_generating", lang))
            
        try:
            # [SAFE LOGGING ADDITION]
            try:
                from core.ai_usage_logger import log_ai_usage
                log_ai_usage(bot, user_id, "workout", 2500)
            except: pass

            # Retry Loop for Robustness
            max_retries = 3
            data = None
            
            for attempt in range(max_retries):
                try:
                    try:
                        bot.edit_message_text(get_text("wait_generating", lang), user_id, msg.message_id) # Safe edit
                    except: pass
                    
                    # [SMART CONTEXT INJECTION]
                    from core.flags import is_flag_enabled
                    from core.context import get_user_context, get_founder_tone_prompt
                    
                    # Create a copy to not mutate DB object
                    user_ctx = dict(user) 
                    
                    extra_ctx = ""
                    if is_flag_enabled("stateful_ai_context", user_id):
                        extra_ctx += get_user_context(user_id)
                        
                    if is_flag_enabled("founder_tone", user_id):
                        extra_ctx += get_founder_tone_prompt()
                        
                    if extra_ctx:
                        user_ctx['goal'] = f"{current_goal}. {extra_ctx}"
                        
                    # Determine Duration
                    plan_type = get_user_plan(user_id)
                    weeks = 4 if plan_type == 'pro' else 1
                    
                    data = ai_generate_weekly_workout_json(user_ctx, lang=lang, duration_weeks=weeks)
                    
                    if data and 'schedule' in data and isinstance(data['schedule'], list):
                        item_count = len(data['schedule'])
                        
                        if item_count >= 5: # Accept at least 5 days (Basic check)
                            break
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                                
                except Exception as e:
                    print(f"workout_gen_attempt_error: {e}")
                    if attempt == max_retries - 1:
                        try:
                            bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, msg.message_id)
                        except: pass
                        return
            
            if not data or 'schedule' not in data:
                bot.edit_message_text(get_text("error_generic", lang), user_id, msg.message_id)
                return

            final_count = len(data['schedule'])
            if final_count < 5:
                 bot.edit_message_text(get_text("error_short_result", lang), user_id, msg.message_id)
                 return

            bot.edit_message_text(get_text("saving_db", lang), user_id, msg.message_id)
            
            try:
                # [PHASE 7.1] Store FULL data to preserve explanation
                template_id = db.create_workout_template(
                    profile_key,
                    json.dumps(data)
                )
            except Exception as e:
                # Fallback update
                template_id = db.update_workout_template_content(
                    profile_key,
                    json.dumps(data)
                )
                if not template_id:
                    exist = db.get_workout_template(profile_key)
                    if exist: template_id = exist['id']
                    else: raise e
            
            db.create_user_workout_link(user_id, template_id)
            
            bot.delete_message(user_id, msg.message_id)
            bot.send_message(user_id, get_text("plan_ready", lang))
            
            new_link = db.get_user_workout_link(user_id)
            db.increment_ai_usage(user_id, 'workout')
            show_daily_workout(bot, user_id, new_link, override_day_idx=1)
                
        except Exception as e:
            print(f"Main Workout Gen Error: {e}")
            try:
                bot.edit_message_text(f"❌ Katta Xatolik: {str(e)[:100]}", user_id, msg.message_id)
            except:
                 pass
    except Exception as e:
         print(f"Outer Gen Error: {e}")
    finally:
                GENERATION_LOCKS.remove(user_id)

def get_exercises_text(schedule_list, day_idx):
    """
    Extract exercise text for a specific day key, stripping URLs.
    Used by handlers for video search and by show_daily_workout for display.
    """
    if not schedule_list or not isinstance(schedule_list, list):
        return ""
        
    total_days = len(schedule_list)
    if day_idx < 1 or day_idx > total_days:
        return ""
        
    try:
        day_data = schedule_list[day_idx - 1]
        text = day_data.get('exercises', '')
        
        # Strip Markdown URLs: [Text](URL) -> Text
        import re
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Strip Raw URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        return text.strip()
    except:
        return ""

def show_daily_workout(bot, user_id, link_data, override_day_idx=None):
    """Render the workout for specific day index."""
    import json
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    from bot.languages import get_text
    
    if not link_data:
        bot.send_message(user_id, "⚠️ Hozircha mashg'ulot rejangiz yo'q. /start ni bosing.")
        return

    lang = db.get_user_language(user_id)
    start_date = link_data['start_date']
    day_idx = link_data['current_day_index']
    
    # Safe date parsing
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
        except:
             try:
                 start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
             except:
                 start_date = datetime.utcnow()

    # Logic: If no override, use DB value. 
    # (Simplified from menu logic, we trust DB or override)
    if override_day_idx is not None:
        day_idx = override_day_idx
        
    try:
        # Load Workout
        # [PHASE 7.1] Support Dict vs List
        data_obj = json.loads(link_data['workout_json'])
        explanation = None
        
        if isinstance(data_obj, dict) and "schedule" in data_obj:
            schedule = data_obj["schedule"]
            explanation = data_obj.get("explanation")
        elif isinstance(data_obj, list):
            schedule = data_obj
        else:
            schedule = []
            
        total_days = len(schedule)
        
        # Boundary checks
        if day_idx < 1: day_idx = 1
        if day_idx > total_days: 
            day_idx = total_days
        
        db.update_workout_day(user_id, day_idx)

        # Find day data
        day_data = None
        idx = day_idx - 1
        if 0 <= idx < total_days:
            day_data = schedule[idx]
        
        if not day_data:
            bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
            return

        # Format Message
        # { "day": 1, "focus": "...", "exercises": "..." }
        
        focus_uu = day_data.get('focus', 'Umumiy')
        
        # Helper map to ensure Uzbek (fallback)
        tr_map = {
            "Upper Body": "Yuqori Tana", 
            "Lower Body": "Pastki Tana",
            "Full Body": "Butun Tana",
            "Core": "Press / Bel",
            "Cardio": "Kardio",
            "Rest": "Dam olish",
            "Dam olish (Rest)": "Dam olish"
        }
        # If the AI returns English, map it. If it returns Uzbek, keep it.
        # Ideally, AI returns Russian if lang=ru, but we can't guarantee it yet.
        # We will assume AI does its job or we leave it as is.
        final_focus = tr_map.get(focus_uu, focus_uu)
        
        txt = f"🏋️ <b>{get_text('workout_title_day', lang, day=day_idx)}</b> (Total {total_days})\n"
        txt += f"{get_text('workout_focus', lang, focus=final_focus)}\n\n"
        
        # Use helper to strip links
        exercises_text = get_exercises_text(schedule, day_idx)
        if not exercises_text:
             exercises_text = day_data.get('exercises', '-')
        
        # REST DAY LOGIC
        if "dam" in final_focus.lower() or "rest" in final_focus.lower() or "отдых" in final_focus.lower():
             import random
             # Use keys for rest messages
             variants = [
                 f"{get_text('rest_day_title', lang)}\n\n{get_text('rest_day_desc', lang)}",
                 f"{get_text('rest_day_tip_1', lang)}",
                 f"{get_text('rest_day_tip_2', lang)}"
             ]
             rest_msg = random.choice(variants)
             txt += f"{rest_msg}\n\n"
             # Show original text if meaningful (like stretching), else hide
             if len(exercises_text) > 20 and "tiklanish" not in exercises_text.lower():
                 txt += f"<i>Qo'shimcha: {_esc(exercises_text)}</i>"
        else:
             # Regular Workout
             txt += f"{_esc(exercises_text)}"
        
        # [SMART PAYWALL]
        from core.context import get_smart_paywall_cta
        if is_flag_enabled("smart_paywall", user_id):
            cta = get_smart_paywall_cta(user_id)
            if cta: txt += cta
            
        # Buttons
        markup = InlineKeyboardMarkup()
        btns = []
            
        if day_idx > 1:
            btns.append(InlineKeyboardButton(get_text("btn_prev", lang), callback_data=f"workout_prev_{day_idx}"))
        
        if day_idx < total_days:
            btns.append(InlineKeyboardButton(get_text("btn_next", lang), callback_data=f"workout_next_{day_idx}"))
            
        markup.row(*btns)
        
        # Regenerate Button
        if day_idx == total_days:
             markup.row(InlineKeyboardButton(get_text("btn_regenerate", lang), callback_data="workout_regenerate"))
        else:
             markup.row(InlineKeyboardButton(get_text("btn_reset", lang), callback_data="workout_regenerate"))
        
        
        # Video tugmasi - Mini Appdagi Mashqlar bo'limiga olib boradi
        mini_app_url = os.getenv("MINI_APP_URL", "https://web-production-b606.up.railway.app")
        if not mini_app_url.endswith("/"): 
            mini_app_url += "/"
        video_webapp_url = f"{mini_app_url}?tab=workout-library"
        markup.row(InlineKeyboardButton("📹 Mashqlar", web_app=types.WebAppInfo(url=video_webapp_url)))
        
        
        # [FEEDBACK V1]
        if is_flag_enabled("feedback_v1", user_id):
            w_id = link_data.get('workout_template_id') or link_data.get('id', 0)
            markup.row(
                InlineKeyboardButton("💪 Juda zo‘r", callback_data=f"fb:workout:strong:{w_id}:{day_idx}"),
                InlineKeyboardButton("😐 Normal", callback_data=f"fb:workout:normal:{w_id}:{day_idx}"),
                InlineKeyboardButton("😴 Og‘ir", callback_data=f"fb:workout:tired:{w_id}:{day_idx}")
            )
            
        # [PHASE 7.1] Explain Engine
        if explanation and is_flag_enabled("phase7_explain_v1", user_id):
            txt += f"\n<i>🔹 {explanation}</i>"
        
        bot.send_message(user_id, txt, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

    except Exception as e:
        print(f"Show Workout Error: {e}")
        try:
             # Need lang here, but might fail if earlier error. default to uz.
             bot.send_message(user_id, "❌ Error opening workout.")
        except: pass

from bot.premium import require_premium

def generate_ai_meal(message, bot, user_id=None):
    """Generate AI meal plan (7-Day JSON System)"""
    from core.ai import ai_generate_weekly_meal_plan_json, get_free_menu_template
    import json
    import time
    
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    # 0. Check Plan
    is_premium = db.is_premium(user_id)
    lang = user.get('language', 'uz')
    
    if not is_premium:
        # FREE TIER LOGIC
        data = get_free_menu_template(lang=lang)
        
        # Save Template
        profile_key = "free_menu_v1"
        try:
             import json
             template_id = db.create_menu_template(profile_key, json.dumps(data['menu']), json.dumps(data['shopping_list']))
        except:
             exist = db.get_menu_template(profile_key)
             template_id = exist['id'] if exist else None
             
        if template_id:
             db.create_user_menu_link(user_id, template_id)
             
             # LOCALIZED
             lang = user.get('language', 'uz')
             bot.send_message(user_id, get_text("free_menu_ready", lang))
             
             # Enhanced Menu Upsell
             markup = types.InlineKeyboardMarkup()
             markup.add(types.InlineKeyboardButton(get_text("btn_get_plus", lang), callback_data="premium_info"))
             
             upsell_msg = get_text("upsell_menu_plus", lang)
             bot.send_message(user_id, upsell_msg, parse_mode="Markdown", reply_markup=markup)
             
             new_link = db.get_user_menu_link(user_id)
             show_daily_menu(bot, user_id, new_link, day_idx=1)
        else:
             lang = user.get('language', 'uz')
             bot.send_message(user_id, get_text("error_template", lang))
        return

    # 0. Check Limit (Premium Only)
    allowed, limit_msg = db.check_ai_gen_limit(user_id, 'menu')
    if not allowed:
        bot.send_message(user_id, limit_msg, parse_mode="Markdown")
        return

    # 0.5 Check Lock
    with LOCKS_MUTEX:
        if user_id in GENERATION_LOCKS:
            bot.send_message(user_id, "⏳ Sabr qiling, reja tuzilmoqda...")
            return
        GENERATION_LOCKS.add(user_id)

    try:
    
        # 1. Check if user already has an active menu link
        # RESTORED: Check for regular users
        active_link = db.get_user_menu_link(user_id)
        if active_link:
            # Auto-open today's menu
            show_daily_menu(bot, user_id, active_link)
            return

        # 2. Build Shared Profile Key (Deduplication)
        age = user.get('age', 25)
        age_band = "18-25"
        if age > 45: age_band = "46+"
        elif age > 35: age_band = "36-45"
        elif age > 25: age_band = "26-35"
            
        profile_key = f"menu_v2_{user.get('gender')}_{user.get('goal')}_{user.get('activity_level')}_{user.get('allergies')}_{age_band}".replace(" ", "_").lower()
        
        # 3. Check for Existing Shared Template
        existing_template = db.get_menu_template(profile_key)
        
        if existing_template:
            bot.send_message(user_id, "💡 Sizga mos tayyor menyu topildi! Yuklanmoqda...")
            db.create_user_menu_link(user_id, existing_template['id'])
            
            new_link = db.get_user_menu_link(user_id)
            db.increment_ai_usage(user_id, 'menu')
            show_daily_menu(bot, user_id, new_link, day_idx=1)
            return

        # If no template, generate new
        # If no template, generate new
        msg = bot.send_message(user_id, get_text("process_started", lang) + "\n\n" + get_text("wait_generating", lang), parse_mode="Markdown")
            
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            # log_ai_usage(bot, user_id, "menu", 2000) # Disabled to prevent double logging with core/ai.py
        except: pass
            
        try:
            # Retry Loop for Robustness (Force 30 days)
            max_retries = 3
            data = None
            
            for attempt in range(max_retries):
                try:
                    try:
                        bot.edit_message_text(get_text("wait_generating", lang), user_id, msg.message_id)
                    except: pass
                    
                    # [SMART CONTEXT INJECTION]
                    from core.flags import is_flag_enabled
                    from core.context import get_user_context, get_founder_tone_prompt
                    
                    user_ctx = dict(user) 
                    
                    # Calculate target
                    # Simplified calc for bot
                    bmr = (10 * user.get('weight', 70)) + (6.25 * user.get('height', 170)) - (5 * user.get('age', 25))
                    if user.get('gender') == 'male': bmr += 5
                    else: bmr -= 161
                    
                    mult = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}.get(user.get('activity_level'), 1.375)
                    target = int(bmr * mult)
                    if user.get('goal') == 'lose': target -= 500
                    elif user.get('goal') == 'gain': target += 300

                    # Determine Duration
                    plan_type = get_user_plan(user_id)
                    weeks = 4 if plan_type == 'pro' else 1

                    data = ai_generate_weekly_meal_plan_json(user_ctx, daily_target=target, lang=lang, duration_weeks=weeks)
                    
                    if data and 'menu' in data and isinstance(data['menu'], list):
                        item_count = len(data['menu'])
                        
                        if item_count >= 7: 
                            break
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                                
                except Exception as e:
                    print(f"gen_attempt_error: {e}")
                    if attempt == max_retries - 1:
                        try:
                            bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, msg.message_id)
                        except: pass
                        return
            
            if not data or 'menu' not in data:
                try:
                    bot.edit_message_text(get_text("error_generic", lang), user_id, msg.message_id)
                except: pass
                return

            final_count = len(data['menu'])
            if final_count < 5:
                 try:
                    bot.edit_message_text(get_text("error_short_result", lang), user_id, msg.message_id)
                 except: pass
                 return

            try:
                bot.edit_message_text(get_text("saving_db", lang), user_id, msg.message_id)
            except: pass
            
            try:
                # [PHASE 7.1] Store FULL data to preserve explanation
                template_id = db.create_menu_template(
                    profile_key,
                    json.dumps(data), 
                    json.dumps(data['shopping_list'])
                )
            except Exception as e:
                # Fallback update
                template_id = db.update_menu_template_content(
                    profile_key,
                    json.dumps(data),
                    json.dumps(data['shopping_list'])
                )
                if not template_id:
                    exist = db.get_menu_template(profile_key)
                    if exist: template_id = exist['id']
                    else: raise e
            
            db.create_user_menu_link(user_id, template_id)
            
            # [NEW] USDA Post-processing
            try:
                # process_menu_nutrition accepts List or Dict? 
                # Assuming it needs List structure string. 
                # Let's inspect process_menu_nutrition usage. It says json.dumps(data['menu']) originally.
                # So we pass data['menu'] here.
                processed_menu_list_str = process_menu_nutrition(json.dumps(data['menu']))
                processed_menu_list = json.loads(processed_menu_list_str)
                
                # Update data object
                data['menu'] = processed_menu_list
                
                # Update DB with full object
                db.update_menu_template_content(profile_key, json.dumps(data), json.dumps(data['shopping_list']))
                print(f"DEBUG: Menu nutrition post-processed for user {user_id}")
            except Exception as nutrition_err:
                print(f"Nutrition Post-process Error: {nutrition_err}")

            try:
                bot.delete_message(user_id, msg.message_id)
            except: pass
            bot.send_message(user_id, get_text("plan_ready", lang))
            
            new_link = db.get_user_menu_link(user_id)
            db.increment_ai_usage(user_id, 'menu')
            show_daily_menu(bot, user_id, new_link, day_idx=1)
                
        except Exception as e:
            print(f"Main Gen Error: {e}")
            try:
                bot.edit_message_text(f"❌ Katta Xatolik: {str(e)[:100]}", user_id, msg.message_id)
            except:
                 pass
    finally:
        with LOCKS_MUTEX:
            if user_id in GENERATION_LOCKS:
                GENERATION_LOCKS.remove(user_id)

def get_weekday_name(date_obj):
    # 0=Mon, ... 3=Thu ...
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    return days[date_obj.weekday()]

def _esc(text):
    """Helper to escape HTML characters"""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def show_daily_menu(bot, user_id, link_data, day_idx=None, meal_type='breakfast'):
    """
    Render a specific meal for a specific day.
    meal_type: 'breakfast', 'lunch', 'dinner', 'snack'
    """
    import json
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    from bot.languages import get_text
    
    start_date = link_data['start_date']
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
        except:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            except:
                start_date = datetime.utcnow()
    
    if day_idx is None:
        # Calculate current day based on start date
        today = datetime.utcnow()
        delta = today - start_date
        day_idx = delta.days + 1
    
    try:
        # [PHASE 7.1] Support Dict vs List
        raw_json = json.loads(link_data['menu_json'])
        explanation = None
        
        if isinstance(raw_json, dict) and "menu" in raw_json:
             menu_list = raw_json["menu"]
             explanation = raw_json.get("explanation")
        elif isinstance(raw_json, list):
             menu_list = raw_json
        else:
             menu_list = []
             
        total_days = len(menu_list)
        
        if day_idx < 1: day_idx = 1
        if day_idx > total_days: day_idx = total_days
        
        # Update current day in DB
        db.update_menu_day(user_id, day_idx)

        idx = day_idx - 1
        day_data = menu_list[idx] if 0 <= idx < total_days else None
        
        if not day_data:
            bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
            return

        # NEW: The AI JSON has a 'meals' field. Check for it.
        meals_root = day_data.get('meals', day_data)

        # Prepare formatting data
        current_view_date = start_date + timedelta(days=day_idx-1)
        weekday_name = get_weekday_name(current_view_date)
        user_lang = db.get_user_language(user_id)
        user_goal = db.get_user(user_id).get('goal', 'Sog\'lom Hayot')
        
        # Translate goal (Quick map)
        if user_lang == 'ru':
            goal_map = {"weight_loss": "Похудение", "muscle_gain": "Набор массы", "health": "Здоровье"}
        else:
            goal_map = {"weight_loss": "Vazn yo'qotish", "muscle_gain": "Mushak o'stirish", "health": "Sog'lom turmush"}
        user_goal = goal_map.get(user_goal, user_goal)

        # 1. Header
        txt = f"🍽 <b>{get_text('menu_header_day', user_lang, day=day_idx)}</b>\n"
        
        goal_label = get_text("goal", user_lang)
        txt += f"🎯 <b>{goal_label}:</b> {_esc(user_goal)} | 📅 {weekday_name}\n\n"
        
        # 2. Meal Content
        meal_data = meals_root.get(meal_type)
        
        meal_labels = {
            'breakfast': get_text('meal_breakfast', user_lang),
            'lunch': get_text('meal_lunch', user_lang),
            'dinner': get_text('meal_dinner', user_lang),
            'snack': get_text('meal_snack', user_lang)
        }
        
        label = meal_labels.get(meal_type, meal_type.title())
        
        if isinstance(meal_data, dict):
            title = meal_data.get('title', 'Noma\'lum taom')
            kcal = meal_data.get('calories', 0)
            
            txt += f"{label}: {_esc(title)}\n"
            if kcal: txt += f"🔥 {kcal} kkal\n\n"
            
            # Ingredients
            ings = meal_data.get('items', [])
            if ings:
                label_ings = get_text("ingredients", user_lang)
                safe_ings = [_esc(i) for i in ings]
                txt += f"<b>{label_ings}:</b> " + ", ".join(safe_ings) + "\n\n"
            
            # Steps
            steps = meal_data.get('steps', [])
            if steps:
                label_prep = get_text("preparation", user_lang)
                txt += f"<b>{label_prep}:</b>\n"
                for i, step in enumerate(steps, 1):
                    txt += f"{i}. {_esc(step)}\n"
                txt += "\n"
        else:
             none_text = get_text("error_no_data", user_lang)
             safe_val = _esc(meal_data) if isinstance(meal_data, str) else none_text
             txt += f"{label}: {safe_val}\n"

        markup = InlineKeyboardMarkup()
        
        # Helper to get other meals
        all_types = ['breakfast', 'lunch', 'dinner', 'snack']
        other_meals = [mt for mt in all_types if mt != meal_type]
        
        # Prepare Navigation Buttons
        nav_btns = []
        for mt in other_meals:
            label = meal_labels.get(mt, mt.capitalize())
            # Shorten labels for compact layout if needed (optional)
            nav_btns.append(InlineKeyboardButton(label, callback_data=f"menu_view_{day_idx}_{mt}"))
            
        # Row 1: Eat + First Nav Meal
        eat_btn = get_text("btn_eaten", user_lang)
        row1 = [InlineKeyboardButton(eat_btn, callback_data=f"eat_{day_idx}_{meal_type}")]
        if nav_btns:
            row1.append(nav_btns[0])
        markup.row(*row1)
        
        # Row 2: Remaining Nav Meals (usually 2 buttons)
        markup.row(*nav_btns[1:])
        
        # Row 3: Swap + Day Navigation
        row3 = []
        row3.append(InlineKeyboardButton(get_text("btn_swap", user_lang), callback_data=f"menu_swap_vip_{day_idx}_{meal_type}"))
        
        # Day Nav Logic (Prioritize Next, else Prev)
        if day_idx < total_days:
            row3.append(InlineKeyboardButton(get_text("menu_next_day", user_lang), callback_data=f"menu_view_{day_idx+1}_{meal_type}"))
        elif day_idx > 1:
            row3.append(InlineKeyboardButton(get_text("menu_prev_day", user_lang), callback_data=f"menu_view_{day_idx-1}_{meal_type}"))
            
        markup.row(*row3)
        
        # Optional Row 4: If we missed a Prev button because we showed Next?
        # User requested specific grid. Let's stick to 3 rows if possible, but navigating BACK is important.
        # If we have both Next and Prev available, Row 3 only shows Next.
        # Let's add Row 4 for Prev if it exists and wasn't shown?
        # User pattern "Almashtirish - Ertaga" implies strict 2 cols. 
        # Making Prev button full width on Row 4 if needed.
        if day_idx > 1 and day_idx < total_days:
             markup.row(InlineKeyboardButton(get_text("menu_prev_day", user_lang), callback_data=f"menu_view_{day_idx-1}_{meal_type}"))

        # [FEEDBACK V1]
        if is_flag_enabled("feedback_v1", user_id):
            t_id = link_data.get('menu_template_id') or link_data.get('id', 0)
            markup.row(
                InlineKeyboardButton("👍", callback_data=f"fb:menu:good:{t_id}:{day_idx}"),
                InlineKeyboardButton("👌", callback_data=f"fb:menu:ok:{t_id}:{day_idx}"),
                InlineKeyboardButton("👎", callback_data=f"fb:menu:bad:{t_id}:{day_idx}")
            )
        
        # [PHASE 7.1] Explain Engine
        if explanation and is_flag_enabled("phase7_explain_v1", user_id):
            txt += f"\n<i>🔹 {explanation}</i>"

        bot.send_message(user_id, txt, parse_mode="HTML", reply_markup=markup)

    except Exception as e:
        print(f"Show Menu Error: {e}")
        bot.send_message(user_id, "❌ Menyu ochishda xatolik.")

def handle_menu_callback(call, bot):
    """
    Handles menu navigation callbacks:
    - menu_view_{day}_{meal_type}
    - eat_{day}_{meal_type}
    """
    user_id = call.from_user.id
    data = call.data
    
    if data.startswith("menu_view_"):
        parts = data.split("_")
        # menu_view_1_lunch
        if len(parts) >= 4:
            day_idx = int(parts[2])
            meal_type = parts[3]
            
            link = db.get_user_menu_link(user_id)
            if link:
                # Delete previous message to keep chat clean (simulating app-like feel)
                try:
                    bot.delete_message(user_id, call.message.message_id)
                except: pass
                
                show_daily_menu(bot, user_id, link, day_idx, meal_type)
        return

    if data.startswith("eat_"):
        # eat_1_breakfast
        parts = data.split("_")
        if len(parts) >= 3:
            day_idx = int(parts[1])
            meal_type = parts[2]
            
            link = db.get_user_menu_link(user_id)
            if not link:
                bot.answer_callback_query(call.id, "❌ Menyu topilmadi!")
                return
                
            # 1. Get Meal Data
            try:
                import json
                raw_json = json.loads(link['menu_json'])
                
                # Handle both dict and list formats
                if isinstance(raw_json, dict) and "menu" in raw_json:
                    menu_list = raw_json["menu"]
                elif isinstance(raw_json, list):
                    menu_list = raw_json
                else:
                    menu_list = []
                
                # Get day data (day_idx is 1-indexed)
                idx = day_idx - 1
                day_data = menu_list[idx] if 0 <= idx < len(menu_list) else None
                
                if not day_data:
                    bot.answer_callback_query(call.id, "❌ Kun ma'lumoti yo'q")
                    return
                
                # Get Meal Kcal
                meals_root = day_data.get('meals', day_data)
                meal_obj = meals_root.get(meal_type)
                kcal = 0
                if meal_obj and isinstance(meal_obj, dict):
                    kcal = meal_obj.get('calories', meal_obj.get('kcal', 0))
                
                if kcal > 0:
                    # 2. Add to Daily Log
                    new_total = db.add_daily_calories(user_id, kcal)
                    
                    # 3. Feedback
                    bot.answer_callback_query(call.id, f"😋 {kcal} kkal qo'shildi!\nJami bugun: {new_total} kkal", show_alert=True)
                    
                    # Optional: Edit button to show checkmark? 
                    # For now just alert is enough to keep complexity low and avoid race conditions with view_menu
                else:
                    bot.answer_callback_query(call.id, "⚠️ Bu ovqatda kaloriya ko'rsatilmagan.")
                    
            except Exception as e:
                print(f"Eat Logic Error: {e}")
                bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi")
        return

    if data == "menu_fridge":
         user_id = call.from_user.id
         
         # 1. Premium Check
         if not db.is_premium(user_id):
             markup = types.InlineKeyboardMarkup()
             markup.add(types.InlineKeyboardButton("👉 Plus’ga o‘ting", callback_data="premium_info"))
             
             msg = "🥦 **Muzlatgich funksiyasi faqat YASHA Plus’da.**\n\n"
             msg += "Bor mahsulotlardan retsept tuzish uchun Premium oling."
             
             bot.send_message(user_id, msg, parse_mode="Markdown", reply_markup=markup)
             bot.answer_callback_query(call.id, "Faqat YASHA Plus uchun", show_alert=True)
             return

         # 2. Set State
         from bot.calorie_scanner import STATE_FRIDGE_INPUT
         from bot import onboarding
         
         onboarding.manager.set_state(user_id, STATE_FRIDGE_INPUT)
         
         bot.send_message(
             user_id, 
             "🥦 **Muzlatgichda nima bor?**\n\nBor mahsulotlarni vergul bilan yozib yuboring.\nMasalan: _Tuxum, pomidor, kartoshka_",
             parse_mode="Markdown"
         )
         bot.answer_callback_query(call.id)
         return
         
    if data.startswith("menu_swap_vip_"):
        # menu_swap_vip_1_breakfast
        user_id = call.from_user.id
        
        # 1. VIP Check (STRICT)
        user_data = db.get_user(user_id)
        # Check if plan_type is explicitly 'vip'
        is_vip = user_data and user_data.get('plan_type') == 'vip'
        
        if not is_vip:
             bot.answer_callback_query(call.id, "🔒 Faqat VIP foydalanuvchilar almashtirish huquqiga ega!", show_alert=True)
             # Send upsell message
             # bot.send_message(user_id, "💎 Taomni almashtirish uchun VIP tarifiga o'ting...", reply_markup=...)
             return

        parts = data.split("_")
        if len(parts) >= 4:
            day_idx = int(parts[3])
            meal_type = parts[4]
            
            # 2. Tell user to wait
            bot.answer_callback_query(call.id, "🔄 Alternativ qidirilmoqda...", show_alert=False)
            wait_msg = bot.send_message(user_id, "👨‍🍳 AI yangi retsept o'ylayapti... (15-20 soniya)")
            
            try:
                # 3. Get User Profile
                user_data = db.get_user(user_id)
                if not user_data:
                    bot.answer_callback_query(call.id, "❌ Profil topilmadi")
                    return

                # 4. Generate New Meal
                from core import ai
                new_meal = ai.ai_generate_single_meal(user_data, meal_type, day_name=f"Kun {day_idx}")
                
                if new_meal:
                    # 5. Update DB
                    success = db.update_single_meal(user_id, day_idx, meal_type, new_meal)
                    
                    if success:
                        # 6. Refresh View
                        try:
                            bot.delete_message(user_id, wait_msg.message_id) # Delete wait msg
                            bot.delete_message(user_id, call.message.message_id) # Delete old menu
                        except: pass
                        
                        link = db.get_user_menu_link(user_id)
                        show_daily_menu(bot, user_id, link, day_idx, meal_type)
                    else:
                        bot.edit_message_text("❌ Saqlashda xatolik.", user_id, wait_msg.message_id)
                else:
                    bot.edit_message_text("❌ AI javob bermadi. Keyinroq urinib ko'ring.", user_id, wait_msg.message_id)
                    
            except Exception as e:
                print(f"Swap Error: {e}")
                try:
                    bot.edit_message_text("❌ Xatolik yuz berdi.", user_id, wait_msg.message_id)
                except:
                    bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi")
        return
         
    if data == "menu_regenerate":
        bot.answer_callback_query(call.id, "🔄 Yangi reja tuzish tez orada!", show_alert=True)
        return
