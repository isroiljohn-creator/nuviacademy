
import datetime
from core.db import db
from core.flags import is_flag_enabled

def get_user_context(user_id: int) -> str:
    """
    Returns a short, read-only summary of user context for AI prompts.
    Guarded by 'stateful_ai_context' flag internally? 
    No, caller should check flag. This just fetches data.
    """
    try:
        # 1. Fetch Basic Stats
        # We can reuse get_user or get_stats but specific is better
        user = db.get_user(user_id)
        if not user:
            return ""

        now = datetime.datetime.now()
        
        # Streak
        streak = user.get('streak', 0)
        
        # Days since join
        join_date = user.get('created_at')
        days_joined = (now - join_date).days if join_date else 0
        
        # Consistency (Simple metric: streak / days_joined or similar)
        # Or just use the raw streak
        
        # Last Active (Check daily logs if possible, or updated_at)
        # We don't have exact 'last_workout' in User model, but we have 'updated_at' or we can query daily_log
        # For MVP speed, let's use streak and goal.
        
        goal = user.get('goal', 'General Fitness')
        
        context_str = (
            f"USER CONTEXT:\n"
            f"- Goal: {goal}\n"
            f"- Current Streak: {streak} days\n"
            f"- Member since: {days_joined} days ago\n"
        )
        
        # Optional: Add recent activity if we wanted to query daily_logs
        # logs = db.get_user_logs(user_id, limit=3)
        # ...
        
        return context_str
        
    except Exception as e:
        print(f"Context Fetch Error: {e}")
        return ""

def get_founder_tone_prompt() -> str:
    """
    Returns the Founder Persona system prompt block.
    """
    return (
        "\n\n[TONE: FOUNDER MODE]\n"
        "speak not as a generic AI, but as a supportive, realistic, and honest human coach.\n"
        "Use 'I' instead of 'We'. Be direct but kind.\n"
        "Acknowledge the difficulty. Use phrases like 'I know this is hard', 'Most people quit here'.\n"
        "Do not sound robotic or overly enthusiastic. Be grounded.\n"
    )

def get_smart_paywall_cta(user_id: int) -> str:
    """
    Returns a smart CTA based on user stats, if Smart Paywall is enabled.
    """
    if not is_flag_enabled("smart_paywall", user_id):
        return ""
        
    try:
        user = db.get_user(user_id)
        if not user: return ""
        
        # Don't show if already premium
        # We need to check premium carefully
        if db.is_premium(user_id):
            return ""
            
        streak = user.get('streak', 0)
        
        if streak >= 5:
            return (
                f"\n\n🔥 **{streak} kunlik STREAK!**\n"
                "Siz ajoyib natija ko'rsatyapsiz. Odatda 7-kuni motivatsiya tushib ketadi.\n"
                "Premium bilan natijangizni sug'urtalang va davom eting. 🛡️"
            )
            
        return ""
        
    except Exception:
        return ""
