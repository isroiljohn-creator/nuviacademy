import json
import os
from telebot import types
from core.db import db

TEMPLATES_DIR = "templates"

def load_template(category, template_id):
    """Load a template from JSON file"""
    filepath = os.path.join(TEMPLATES_DIR, category, f"{template_id}.json")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_workout_templates():
    """Get list of available workout templates"""
    return [
        {"id": "beginner_home", "name": "🏠 Uy mashqlari (Boshlang'ich)", "emoji": "🏠"},
        {"id": "weight_loss", "name": "🔥 Vazn yo'qotish rejasi", "emoji": "🔥"},
        {"id": "muscle_gain", "name": "💪 Mushak massa oshirish", "emoji": "💪"}
    ]

def get_meal_templates():
    """Get list of available meal templates"""
    return [
        {"id": "meal_1500", "name": "🍏 Vazn yo'qotish (1500 kcal)", "emoji": "🍏"},
        {"id": "meal_2000", "name": "🥗 Sog'lom ovqatlanish (2000 kcal)", "emoji": "🥗"},
        {"id": "meal_2500", "name": "💪 Mushak oshirish (2500 kcal)", "emoji": "💪"}
    ]

def show_workout_template_menu(message, bot):
    """Show workout template selection menu"""
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    is_premium = db.is_premium(user_id)
    
    from bot.languages import get_text
    
    title = get_text("workout_templates_title", lang)
    desc = get_text("workout_templates_desc", lang)
    
    text = f"{title}\n\n{desc}"
    
    if not is_premium:
        text += f"💡 *{get_text('premium_required_upsell', lang)}*"
    
    markup = types.InlineKeyboardMarkup()
    
    # Add template options
    for template in get_workout_templates():
        # Note: template names are hardcoded in get_workout_templates, 
        # but we could localize those too if needed. 
        # For now, focusing on the menu structure.
        markup.add(types.InlineKeyboardButton(
            template["name"],
            callback_data=f"workout_template_{template['id']}"
        ))
    
    # Add AI option for premium users
    if is_premium:
        markup.add(types.InlineKeyboardButton(
            get_text("btn_get_plus_ai", lang),
            callback_data="workout_ai"
        ))
    else:
        # Upsell premium
        markup.add(types.InlineKeyboardButton(
            get_text("btn_get_plus_ai_locked", lang),
            callback_data="upgrade_premium"
        ))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def show_meal_template_menu(message, bot):
    """Show meal template selection menu"""
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    is_premium = db.is_premium(user_id)
    
    from bot.languages import get_text
    
    title = get_text("meal_templates_title", lang)
    desc = get_text("meal_templates_desc", lang)
    
    text = f"{title}\n\n{desc}"
    
    if not is_premium:
        text += f"💡 *{get_text('premium_required_upsell', lang)}*"
    
    markup = types.InlineKeyboardMarkup()
    
    # Add template options
    for template in get_meal_templates():
        markup.add(types.InlineKeyboardButton(
            template["name"],
            callback_data=f"meal_template_{template['id']}"
        ))
    
    # Add AI option for premium users
    if is_premium:
        markup.add(types.InlineKeyboardButton(
            get_text("btn_get_plus_ai", lang),
            callback_data="meal_ai"
        ))
    else:
        # Upsell premium
        markup.add(types.InlineKeyboardButton(
            get_text("btn_get_plus_ai_locked", lang),
            callback_data="upgrade_premium"
        ))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def send_template_plan(user_id, category, template_id, bot):
    """Load and send a template plan"""
    lang = db.get_user_language(user_id)
    template = load_template(category, template_id)
    
    from bot.languages import get_text
    
    if not template:
        bot.send_message(user_id, get_text("template_not_found", lang))
        return
    
    plan_text = template["plan"]
    
    # Send the plan
    try:
        from core.utils import safe_split_text, strip_html
        
        chunks = safe_split_text(plan_text)
        
        for chunk in chunks:
            try:
                bot.send_message(user_id, chunk, parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, strip_html(chunk))
        
        # Log Event [NEW]
        db.log_event(user_id, f"{category[:-1]}_template_viewed", {"template_id": template_id})

        
        # Add feedback message
        bot.send_message(
            user_id,
            get_text("template_sent_success", lang) + get_text("template_ai_suggestion", lang),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending template: {e}")
        bot.send_message(user_id, strip_html(plan_text))

def register_handlers(bot):
    """Register all template-related callback handlers"""
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("workout_template_"))
    def handle_workout_template(call):
        template_id = call.data.replace("workout_template_", "")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_template_plan(call.from_user.id, "workouts", template_id, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("meal_template_"))
    def handle_meal_template(call):
        template_id = call.data.replace("meal_template_", "")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_template_plan(call.from_user.id, "meals", template_id, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data == "upgrade_premium")
    def handle_upgrade_button(call):
        print(f"DEBUG: upgrade_premium button clicked by {call.from_user.id}")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        from bot.premium import handle_premium_menu
        print(f"DEBUG: Redirecting to premium menu")
        handle_premium_menu(call.message, bot, user_id=call.from_user.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "workout_ai")
    def handle_workout_ai_request(call):
        print(f"DEBUG: workout_ai button clicked by {call.from_user.id}")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Import here to avoid circular dependency
        from bot.workout import generate_ai_workout
        print(f"DEBUG: Generating AI workout")
        generate_ai_workout(call.message, bot, user_id=call.from_user.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "meal_ai")
    def handle_meal_ai_request(call):
        print(f"DEBUG: meal_ai button clicked by {call.from_user.id}")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        from bot.workout import generate_ai_meal
        print(f"DEBUG: Generating AI meal")
        generate_ai_meal(call.message, bot, user_id=call.from_user.id)

