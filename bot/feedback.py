from telebot import types
from datetime import datetime
from sqlalchemy import text
from backend.database import get_sync_db
from backend.models import MenuFeedback, WorkoutFeedback, CoachFeedback
from core.flags import is_flag_enabled
from core.coach import get_coach_message, get_mock_context
from core.db import db
import logging

logger = logging.getLogger(__name__)

def handle_feedback_callback(call, bot):
    """
    Handles callbacks starting with fb:
    fb:menu:RATING:ID:DAY
    fb:workout:RATING:ID:DAY
    fb:coach:REACTION:KEY
    """
    user_id = call.from_user.id
    if not is_flag_enabled("feedback_v1", user_id):
        bot.answer_callback_query(call.id, "Feedback currently disabled.")
        return

    data = call.data
    parts = data.split(":")
    
    try:
        if parts[1] == "menu":
            # fb:menu:good:123:1
            rating = parts[2]
            menu_id = int(parts[3]) if parts[3].isdigit() else None
            day_idx = int(parts[4]) if parts[4].isdigit() else None
            
            with get_sync_db() as session:
                fb = MenuFeedback(
                    user_id=user_id,
                    menu_template_id=menu_id,
                    day_index=day_idx,
                    rating=rating
                )
                session.add(fb)
                session.commit()
                
            bot.answer_callback_query(call.id, "✅ Qabul qilindi!")
            # Optional: Disable buttons (edit message)
            # For now, just ack.
            
            # Log Admin Event (Phase 6 Req)
            try:
                db.log_event(user_id, "FEEDBACK_SAVED", {"type": "menu", "rating": rating, "id": menu_id})
            except: pass
            
        elif parts[1] == "workout":
            # fb:workout:strong:123:1
            rating = parts[2]
            plan_id = int(parts[3]) if parts[3].isdigit() else None
            day_idx = int(parts[4]) if parts[4].isdigit() else None
            
            with get_sync_db() as session:
                fb = WorkoutFeedback(
                    user_id=user_id,
                    workout_plan_id=plan_id,
                    day_index=day_idx,
                    rating=rating
                )
                session.add(fb)
                session.commit()
            
            try:
                db.log_event(user_id, "FEEDBACK_SAVED", {"type": "workout", "rating": rating, "id": plan_id})
            except: pass

            bot.answer_callback_query(call.id, "✅ Kuch bo'lsin!")
            
        elif parts[1] == "coach":
            # fb:coach:like:KEY
            reaction = parts[2]
            key = ":".join(parts[3:]) # Key might contain colons
            category = key.split(":")[0] if ":" in key else "UNKNOWN"
            
            with get_sync_db() as session:
                fb = CoachFeedback(
                    user_id=user_id,
                    coach_msg_key=key,
                    category=category,
                    reaction=reaction
                )
                session.add(fb)
                session.commit()
                
            try:
                db.log_event(user_id, "FEEDBACK_SAVED", {"type": "coach", "reaction": reaction, "key": key})
            except: pass

            bot.answer_callback_query(call.id, "Rahmat!")
    except Exception as e:
        logger.error(f"Feedback Error: {e}")
        bot.answer_callback_query(call.id, "Error saving feedback.")

def send_coach_message_with_feedback(bot, user_id):
    """
    Fetches context, gets message from core logic, and sends with buttons.
    """
    user = db.get_user(user_id) # Dict or object? core/db returns dict
    # We need a User object for get_mock_context if we want to use that, OR passing dict is fine if updated.
    # get_coach_message expects dict context.
    
    # Simulating context for now since we don't have full ActivityLogs query logic handy in 1 turn.
    # We use what we have in DB user (streaks).
    # Inactivity needs last_checkin parsing, let's assume Mock/Basic context for now.
    
    # Re-fetch user model instance for helper
    with get_sync_db() as session:
        from backend.models import User
        u = session.query(User).filter(User.telegram_id == user_id).first()
        if not u: return
        ctx = get_mock_context(u)
    
    # Call core logic
    result = get_coach_message(user_id, ctx)
    if not result:
        return # No message triggers
        
    # Result is now (msg, key, category)
    if isinstance(result, tuple) and len(result) == 3:
        text, key, cat = result
    else:
        # Backward compat if not updated or single return
        text = str(result)
        key = "UNKNOWN:0"
    
    # Send
    markup = types.InlineKeyboardMarkup()
    if is_flag_enabled("feedback_v1", user_id):
        markup.row(
            types.InlineKeyboardButton("👍", callback_data=f"fb:coach:like:{key}"),
            types.InlineKeyboardButton("❤️", callback_data=f"fb:coach:love:{key}"),
            types.InlineKeyboardButton("😐", callback_data=f"fb:coach:meh:{key}")
        )
        
    bot.send_message(user_id, f"💡 <b>Coach Zone</b>\n\n{text}", parse_mode="HTML", reply_markup=markup)

def get_feedback_analytics():
    """
    Returns string summary for admin with investor-grade metrics.
    """
    with get_sync_db() as session:
        # 1. Feedback Coverage (Unique Users)
        coverage_sql = text("""
            SELECT COUNT(DISTINCT user_id)
            FROM (
              SELECT user_id FROM menu_feedback WHERE created_at >= now() - interval '7 days'
              UNION
              SELECT user_id FROM workout_feedback WHERE created_at >= now() - interval '7 days'
              UNION
              SELECT user_id FROM coach_feedback WHERE created_at >= now() - interval '7 days'
            ) t;
        """)
        unique_users = session.execute(coverage_sql).scalar() or 0
        
        # 2. Menu Feedback Distribution
        menu_stats = session.execute(text("SELECT rating, COUNT(*) FROM menu_feedback WHERE created_at >= now() - interval '7 days' GROUP BY 1")).fetchall()
        menu_str = ", ".join([f"{r[0]}: {r[1]}" for r in menu_stats]) or "No data"
        
        # 3. Workout Feedback Distribution
        workout_stats = session.execute(text("SELECT rating, COUNT(*) FROM workout_feedback WHERE created_at >= now() - interval '7 days' GROUP BY 1")).fetchall()
        work_str = ", ".join([f"{r[0]}: {r[1]}" for r in workout_stats]) or "No data"
        
        # 4. Coach Zone Reaction Performance
        coach_stats = session.execute(text("SELECT reaction, COUNT(*) FROM coach_feedback WHERE created_at >= now() - interval '7 days' GROUP BY 1")).fetchall()
        coach_str = ", ".join([f"{r[0]}: {r[1]}" for r in coach_stats]) or "No data"
        
        # 5. TOP 10 Coach Messages (Loved)
        top_coach_sql = text("""
            SELECT coach_msg_key, category, COUNT(*) AS love_count
            FROM coach_feedback
            WHERE reaction = 'love'
            GROUP BY coach_msg_key, category
            ORDER BY love_count DESC
            LIMIT 10;
        """)
        top_coach = session.execute(top_coach_sql).fetchall()
        top_coach_str = "\n".join([f"- {r[0]} ({r[1]}): {r[2]} ❤️" for r in top_coach]) if top_coach else "No data"
        
    return f"""📊 <b>Feedback Analytics (Last 7 Days)</b>

👥 <b>Coverage:</b> {unique_users} unique users

🥗 <b>Menu Feedback:</b>
{menu_str}

🏋️ <b>Workout Feedback:</b>
{work_str}

💡 <b>Coach Reactions:</b>
{coach_str}

🏆 <b>Top 10 Loved Coach Messages:</b>
{top_coach_str}
"""


def register_handlers(bot):
    """Register feedback callback handlers"""
    @bot.callback_query_handler(func=lambda call: call.data.startswith('fb:'))
    def feedback_callback(call):
        handle_feedback_callback(call, bot)
