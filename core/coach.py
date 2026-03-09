import random
import logging
from datetime import datetime, timedelta
from core.flags import is_flag_enabled
from backend.models import User

logger = logging.getLogger("CoachZone")

# --- CONTENT LIBRARY ---
COACH_MESSAGES = {
    "GENTLE_NUDGE": [
        "Salom! Shunchaki sizdan xabar olmoqchi edim. Kichik qadam ham hisobga o‘tadi. Bugun 1 stakan suv ichishdan boshlaymizmi? 💧",
        "Sizni sog‘indik! Har doim qaytish imkoni bor. Bugun o‘zingiz uchun 5 daqiqa ajrata olasizmi?",
        "Harakat — bu hayot. Kichik bo‘lsa ham, harakat qiling. Biz siz bilanmiz! 🌿",
        "Bugun o‘zingizga vaqt ajratish uchun ajoyib kun. Boshlaymizmi?",
    ],
    "CONSISTENCY_WATER": [
        "Suv ichish bo‘yicha barqarorlikni saqlayapsiz! Bu teringiz va energiyangiz uchun ajoyib. 💧",
        "Qoyil! Suv balansini ushlash — sog‘lomlikning yarmi. Davom eting! 🌊",
        "Suv — hayot manbai. Siz bu manbadan to‘g‘ri foydalanyapsiz. Malades!",
    ],
    "IDENTITY_BUILDER": [
        "Qoyil! Siz allaqachon sog‘lom odat shakllantiryapsiz. Bu intizom sizga yarashadi! 🌟",
        "Siz shunchaki mashq qilmayapsiz, siz o‘z kelajagingizni quryapsiz. Davom eting!",
        "Intizom — bu sizning yangi super kuchingiz. Natijalar uzoq kutdirmaydi! 💪",
        "Har kuni o‘zingizni yengishingiz — bu haqiqiy g‘alaba.",
    ],
    "NORMALIZE_REST": [
        "Dam olish ham mashg‘ulotning bir qismi. Tanangizga quloq soling va kuch yig‘ib oling. Ertaga davom etamiz! 💪",
        "Bugun o‘zingizni majburlamang. Agar charchagan bo‘lsangiz, shunchaki sayr qiling. Bu ham foydali!",
        "Tiklanish jarayoni o‘sish uchun kerak. Yaxshi dam oling!",
    ],
    "CELEBRATION": [
        "Vau! Yangi natija! Siz bu kunni eslab qoling. 🔥",
        "Progress bor! Kichik g‘alabalar katta maqsadlarga olib boradi. Tabriklaymiz! 🎉",
    ],
    "DAILY_WISDOM": [
        "Muvaffaqiyat — bu har kuni qilingan kichik harakatlar yig‘indisi. Bugungi rejangiz qanday?",
        "Eng yaxshi mashq — bu qilingan mashq. Mukammallik shart emas, davomiylik muhim.",
        "Sog‘lom bo‘lish — bu poyga emas, bu sayohat. Zavqlaning! 🌸",
        "Bugun kechagidan ko‘ra yaxshiroq bo‘lish imkoniyati.",
    ]
}

def get_coach_message(user_id: int, user_context: dict) -> str:
    """
    Selects a Coach Zone message based on user context rules.
    NO AI generation.
    Returns None if restricted or no rule matches significant triggger.
    """
    # 1. Feature Flag Check
    if not is_flag_enabled("coach_zone_v1", user_id):
        return None

    # 2. Extract Context
    inactivity_days = user_context.get("inactivity_days", 0)
    streak_water = user_context.get("streak_water", 0)
    streak_workout = user_context.get("streak_workout", 0)
    skipped_workout = user_context.get("skipped_workout", False)
    
    # 3. Rules Engine (Priority Order)
    
    # Rule 1: Inactivity Nudge (High Priority)
    if inactivity_days >= 2:
        return _pick("GENTLE_NUDGE", COACH_MESSAGES["GENTLE_NUDGE"], user_id)
        
    # Rule 2: Missed Workout Support
    if skipped_workout:
        return _pick("NORMALIZE_REST", COACH_MESSAGES["NORMALIZE_REST"], user_id)
        
    # Rule 3: Workout Consistency Celebration
    if streak_workout >= 3:
        return _pick("IDENTITY_BUILDER", COACH_MESSAGES["IDENTITY_BUILDER"], user_id)
        
    # Rule 4: Water Consistency
    if streak_water >= 3:
        return _pick("CONSISTENCY_WATER", COACH_MESSAGES["CONSISTENCY_WATER"], user_id)
        
    # Rule 5: Default Daily Wisdom (Random 30% chance on check-up)
    if random.random() < 0.3:
        return _pick("DAILY_WISDOM", COACH_MESSAGES["DAILY_WISDOM"], user_id)
        
    return None

def _pick(category, msgs, user_id):
    try:
        from core.adaptation import select_coach_message_adapted
        # Attempt adaptation
        res = select_coach_message_adapted(category, user_id)
        if res: return res
    except Exception as e:
        # logging.error(f"Coach adaptation error: {e}")
        pass
        
    # Fallback to random
    if not msgs: return "Salom!", "DEFAULT:0", "DEFAULT"
    idx = random.randrange(len(msgs))
    return msgs[idx], f"{category}:{idx}", category

def get_mock_context(user: User):
    """
    Helper to extract context from User model for testing/usage.
    Real implementation would query ActivityLogs.
    For V1 MVP, we simulate or assume basic fields exist on User model.
    """
    last_checkin_str = getattr(user, "last_checkin", None)
    inactivity = 0
    if last_checkin_str:
        try:
            # Assuming YYYY-MM-DD
            last_date = datetime.strptime(last_checkin_str, "%Y-%m-%d")
            delta = datetime.now() - last_date
            inactivity = delta.days
        except:
            pass
            
    return {
        "inactivity_days": inactivity or 0,
        "streak_water": getattr(user, "streak_water", 0) or 0,
        "streak_workout": getattr(user, "streak_workout", 0) or 0, # Assumes added to model
        "skipped_workout": False # Hard to detect without detailed logs, placeholder
    }
