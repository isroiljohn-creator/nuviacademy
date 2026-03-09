from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import os
from core.config import ADMIN_IDS
from bot.languages import get_text

def language_selection_keyboard():
    """Keyboard for selecting bot language"""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    )
    return markup

def phone_request_keyboard(lang="uz"):
    """Request phone number from user"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_text = get_text("btn_phone_send", lang=lang)
    markup.add(KeyboardButton(btn_text, request_contact=True))
    return markup

def gender_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    male_text = get_text("male", lang=lang)
    female_text = get_text("female", lang=lang)
    markup.row(
        InlineKeyboardButton(male_text, callback_data="gender_male"),
        InlineKeyboardButton(female_text, callback_data="gender_female")
    )
    return markup

def daily_meal_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=2) # Default row width
    
    # 1. Iste'mol qildim (Full width, Main Action) - Using a dedicated row
    markup.row(InlineKeyboardButton(get_text("btn_eaten", lang=lang), callback_data="meal_eaten_choose"))
    
    # 2. Meal Types (Lunch, Dinner) - Side by Side
    markup.add(
        InlineKeyboardButton(get_text("meal_lunch", lang=lang), callback_data="meal_Lunch"),
        InlineKeyboardButton(get_text("meal_dinner", lang=lang), callback_data="meal_Dinner")
    )
    
    # 3. Snack, Prev, Next - 3 in a row
    # To put 3 in a row, we can use row width or markup.row
    markup.row(
        InlineKeyboardButton(get_text("meal_snack", lang=lang), callback_data="meal_Snack"),
        InlineKeyboardButton(get_text("menu_prev_day", lang=lang), callback_data="menu_prev"),
        InlineKeyboardButton(get_text("menu_next_day", lang=lang), callback_data="menu_next")
    )
    
    # 4. Shopping and Swap (Full width or split)
    markup.add(
        InlineKeyboardButton(get_text("btn_shopping_list", lang=lang), callback_data="shopping_list"),
        InlineKeyboardButton(get_text("btn_swap", lang=lang), callback_data="swap_meal_start")
    )
    
    return markup   
def goal_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(get_text("goal_weight_loss", lang=lang), callback_data="goal_weight_loss"))
    markup.add(InlineKeyboardButton(get_text("goal_mass_gain", lang=lang), callback_data="goal_mass_gain"))
    markup.add(InlineKeyboardButton(get_text("goal_health", lang=lang), callback_data="goal_health"))
    return markup

def activity_level_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(get_text("activity_sedentary", lang=lang) + " 🪑", callback_data="activity_sedentary"),
        InlineKeyboardButton(get_text("activity_light", lang=lang) + " 🚶‍♂️", callback_data="activity_light"),
        InlineKeyboardButton(get_text("activity_moderate", lang=lang) + " 🏃‍♂️", callback_data="activity_moderate"),
        InlineKeyboardButton(get_text("activity_active", lang=lang) + " 🏋️‍♂️", callback_data="activity_active"),
        InlineKeyboardButton(get_text("activity_athlete", lang=lang) + " 🔥", callback_data="activity_athlete")
    )
    return markup

def allergy_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    no_text = get_text("no", lang=lang) + " ❌"
    yes_text = get_text("yes", lang=lang) + " ✅"
    markup.row(
        InlineKeyboardButton(no_text, callback_data="allergy_no"),
        InlineKeyboardButton(yes_text, callback_data="allergy_yes")
    )
    return markup

def main_menu_keyboard(is_admin=False, user_id=None, lang=None):
    """
    Generate Main Menu Reply Keyboard.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Calculate admin status securely
    real_admin = False
    if user_id:
        real_admin = int(user_id) in ADMIN_IDS
        if lang is None:
            from core.db import db
            lang = db.get_user_language(user_id)
    
    if lang is None: lang = "uz"

    # Row 1: AI Murabbiy | Ilovani ochish
    # Row 1: AI Murabbiy | Ilovani ochish
    coach_text = get_text("btn_ai_murabbiy", lang=lang)
    app_text = get_text("btn_mini_app", lang=lang)
    
    mini_app_url = os.getenv("MINI_APP_URL") or os.getenv("WEBAPP_URL") or "https://yasha-insights.up.railway.app"
    if mini_app_url.endswith("/"): mini_app_url = mini_app_url[:-1]

    markup.add(
        KeyboardButton(coach_text),
        KeyboardButton(app_text, web_app=WebAppInfo(url=mini_app_url))
    )
    
    # Row 2: Kaloriya tahlili | YASHA Plus
    scan_text = get_text("btn_calorie_tahlili", lang=lang)
    plus_text = get_text("btn_yasha_plus", lang=lang)
    markup.add(KeyboardButton(scan_text), KeyboardButton(plus_text))
    
    # Row 3: Profil | Yordam
    profile_text = get_text("btn_profile", lang=lang)
    help_text = get_text("btn_help", lang=lang)
    markup.add(
        KeyboardButton(profile_text, web_app=WebAppInfo(url=f"{mini_app_url}?tab=profile")),
        KeyboardButton(help_text)
    )
    
    return markup

def plan_inline_keyboard(lang="uz"):
    from bot.languages import get_text
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(get_text("btn_ai_workout", lang=lang), callback_data="plan_ai_workout"),
        InlineKeyboardButton(get_text("btn_ai_meal", lang=lang), callback_data="plan_ai_meal"),
        InlineKeyboardButton(get_text("btn_calorie_scan", lang=lang), callback_data="plan_calorie_scan")
    )
    return markup

def habits_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💧 Suv trekeri", callback_data="habit_water"),
        InlineKeyboardButton("😴 Uyqu trekeri", callback_data="habit_sleep"),
        InlineKeyboardButton("🙂 Kayfiyat trekeri", callback_data="habit_mood"),
        InlineKeyboardButton("🚶🏻 Qadamlar", callback_data="habit_steps"),
        InlineKeyboardButton("📊 Odatlar statistikasi", callback_data="habit_stats")
    )
    return markup

def ai_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("❓ AI savol-javob", callback_data="ai_qa"),
        InlineKeyboardButton("🍳 AI retsept", callback_data="ai_recipe"),
        InlineKeyboardButton("🥦 AI menyu", callback_data="ai_meal"),
        InlineKeyboardButton("🏋️ AI mashq rejasi", callback_data="ai_workout"),
        InlineKeyboardButton("🛒 AI shopping list", callback_data="ai_shopping")
    )
    return markup

def points_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Coinlarim", callback_data="points_balance"),
        InlineKeyboardButton("🎁 Mukofotlar", callback_data="points_rewards"),
        InlineKeyboardButton("📜 Qoidalar", callback_data="points_rules"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="back_premium")
    )
    return markup

def challenges_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📆 Haftalik challenge", callback_data="challenge_weekly"),
        InlineKeyboardButton("🗓 Oylik challenge", callback_data="challenge_monthly"),
        InlineKeyboardButton("👥 Do‘stlar challenge", callback_data="challenge_friends"),
        InlineKeyboardButton("🏆 Leaderboard", callback_data="challenge_leaderboard")
    )
    return markup

def profile_inline_keyboard(lang="uz"):
    from bot.languages import get_text
    markup = InlineKeyboardMarkup(row_width=1)
    
    mini_app_url = os.getenv("MINI_APP_URL") or os.getenv("WEBAPP_URL") or "https://yasha-insights.up.railway.app"
    if mini_app_url.endswith("/"): mini_app_url = mini_app_url[:-1]

    markup.add(
        InlineKeyboardButton(get_text("btn_edit_profile", lang), callback_data="profile_edit"),
        InlineKeyboardButton(get_text("btn_health_stats", lang), web_app=WebAppInfo(url=f"{mini_app_url}?tab=reports"))
    )
    return markup

def premium_inline_keyboard(lang="uz"):
    from bot.languages import get_text
    markup = InlineKeyboardMarkup()
    mini_app_url = os.getenv("MINI_APP_URL") or os.getenv("WEBAPP_URL") or "https://yasha-insights.up.railway.app"
    if mini_app_url.endswith("/"): mini_app_url = mini_app_url[:-1]
    # Main button: Unlock Features (previously Change Plan)
    markup.row(InlineKeyboardButton(get_text("btn_unlock_features", lang), callback_data="premium_buy"))
    # Challenges button (opens Mini App)
    markup.row(InlineKeyboardButton(get_text("btn_challenges_menu", lang), web_app=WebAppInfo(url=f"{mini_app_url}?tab=challenges")))
    return markup

def payment_links_keyboard(lang="uz"):
    """
    Creates inline keyboard with direct payment links for subscription plans.
    URLs are placeholders and should be replaced with real Click/Payme links.
    """
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Plans using callbacks to trigger Telegram Invoice
    plans = [
        {"key": "btn_oylik_plus_price", "callback": "pay_plus_1"},
        {"key": "btn_oylik_pro_price", "callback": "pay_vip_1"},
        {"key": "btn_3oylik_plus_price", "callback": "pay_plus_3"},
        {"key": "btn_3oylik_pro_price", "callback": "pay_vip_3"}
    ]
    
    for plan in plans:
        btn_text = get_text(plan["key"], lang=lang)
        markup.add(InlineKeyboardButton(btn_text, callback_data=plan["callback"]))
    
    return markup

def gamification_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Mashq qildim ✅", callback_data="daily_workout_done"))
    markup.add(InlineKeyboardButton("Suv ichdim 💧", callback_data="daily_water_done"))
    return markup

def ai_coach_submenu_keyboard(lang="uz"):
    """Reply Submenu for '🤖 AI murabbiy' (Legacy - kept for fallback)"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mini_app_url = os.getenv("MINI_APP_URL", "https://yasha-insights.up.railway.app")
    markup.add(KeyboardButton(get_text("btn_workout", lang=lang)), KeyboardButton(get_text("btn_meal", lang=lang)))
    markup.add(KeyboardButton(get_text("btn_ai_recipe", lang=lang)), KeyboardButton(get_text("btn_shopping_list", lang=lang)))
    markup.add(
        KeyboardButton(get_text("btn_ai_qa", lang=lang), web_app=WebAppInfo(url=f"{mini_app_url}?tab=ai-coach")),
        KeyboardButton(get_text("btn_back", lang=lang))
    )
    return markup

def ai_coach_inline_keyboard(lang="uz"):
    """Inline Submenu for '🤖 AI murabbiy'"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        InlineKeyboardButton(get_text("btn_workout_plan", lang=lang), callback_data="ai_sub_workout"),
        InlineKeyboardButton(get_text("btn_meal_plan", lang=lang), callback_data="ai_sub_meal")
    )
    markup.add(
        InlineKeyboardButton(get_text("btn_ai_recipe", lang=lang), callback_data="ai_sub_recipe"),
        InlineKeyboardButton(get_text("btn_shopping_list_kb", lang=lang), callback_data="ai_sub_shopping")
    )
    # Changed QA to open Mini App, Removed Back/Close (user can just swipe or use main menu)
    mini_app_url = os.getenv("MINI_APP_URL") or os.getenv("WEBAPP_URL") or "https://yasha-insights.up.railway.app"
    if mini_app_url.endswith("/"): mini_app_url = mini_app_url[:-1]
    markup.add(
        InlineKeyboardButton(get_text("btn_ai_qa", lang=lang), web_app=WebAppInfo(url=f"{mini_app_url}?tab=ai-coach"))
    )
    return markup

def challenges_submenu_keyboard(lang="uz"):
    """Submenu for '🔥 Chellenjlar'"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton(get_text("btn_challenge_daily", lang=lang)), KeyboardButton(get_text("btn_leaderboard", lang=lang)))
    markup.add(KeyboardButton(get_text("btn_referral_friend", lang=lang)), KeyboardButton(get_text("btn_back", lang=lang)))
    return markup

def help_submenu_keyboard(lang="uz"):
    """Submenu for '📩 Yordam'"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mini_app_url = os.getenv("MINI_APP_URL", "https://yasha-insights.up.railway.app")
    markup.add(
        KeyboardButton(get_text("btn_ask_question", lang=lang), web_app=WebAppInfo(url=f"{mini_app_url}?tab=ai-coach")),
        KeyboardButton(get_text("btn_help_lang", lang=lang))
    )
    markup.add(KeyboardButton(get_text("btn_back", lang=lang)))
    return markup

def admin_analytics_keyboard():
    """Inline keyboard for navigating analytics sections."""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📈 O'sish (Growth)", callback_data="admin_stats_growth"),
        InlineKeyboardButton("🌪 Voronka (Funnel)", callback_data="admin_stats_funnel")
    )
    markup.add(
        InlineKeyboardButton("📉 Retention", callback_data="admin_stats_retention"),
        InlineKeyboardButton("💎 Premium", callback_data="admin_stats_premium")
    )
    markup.add(
        InlineKeyboardButton("🥗 Menu Rollout", callback_data="admin_stats_menu_rollout"),
        InlineKeyboardButton("🏋️ Workout Rollout", callback_data="admin_stats_workout_rollout"),
        InlineKeyboardButton("📸 Calorie Rollout", callback_data="admin_stats_calorie_rollout")
    )
    markup.add(
        InlineKeyboardButton("🔄 Yangilash", callback_data="admin_stats_refresh")
    )
    return markup

def admin_developer_keyboard():

    """
    Main menu for Developers/Admins. Consolidates all /commands into buttons.
    """
    markup = InlineKeyboardMarkup(row_width=2)
    import os
    base_url = os.getenv("MINI_APP_URL", "https://yasha-insights.up.railway.app")
    if base_url.endswith("/"): base_url = base_url[:-1]
    webapp_url = f"{base_url}/admin-insights/"

    markup.row(
        InlineKeyboardButton("🚦 Dashboard", web_app=WebAppInfo(url=webapp_url)),
        InlineKeyboardButton("🗑 AI Bazani Tozalash", callback_data="dev_clear_ai_db")
    )
    markup.row(
        InlineKeyboardButton("👤 Userni o'chirish", callback_data="dev_delete_user_start")
    )
    markup.row(
        InlineKeyboardButton("🚩 Feature Flags", callback_data="dev_flags_menu"),
        InlineKeyboardButton("🧪 AI ni tekshirish", callback_data="dev_test_ai_start")
    )
    return markup
def onboarding_welcome_keyboard(lang="uz"):
    """Keyboard sent after onboarding completion"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(get_text("btn_public_offer", lang=lang), callback_data="show_public_offer"))
    return markup
