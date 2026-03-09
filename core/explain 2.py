import random
import logging
from typing import Optional
from core.flags import is_flag_enabled
from core.db import db

logger = logging.getLogger("ExplainEngine")

EXPLANATION_TEMPLATES = {
    "menu_variant_changed": [
        "So‘nggi baholaringizga qarab menyuni biroz yengillashtirdik. Bu sizga qulayroq bo‘lishi uchun."
    ],
    "menu_kcal_adjusted": [
        "Oxirgi kunlardagi holatingizni hisobga olib kaloriya miqdorini moslashtirdik."
    ],
    "workout_soft_mode_enabled": [
        "Bugun tanangizga yukni kamaytirdik. Harakat — baribir foydali."
    ],
    "meal_swapped": [
        "Kaloriyasi yaqinroq va qulayroq variant tanlandi."
    ]
}

def get_explanation(event_type: str, context: dict) -> Optional[str]:
    """
    Returns a short Uzbek explanation string (1–2 sentences)
    or None if no explanation should be shown.
    """
    user_id = context.get("user_id")
    if not user_id:
        return None
        
    # Flag Check
    if not is_flag_enabled("phase7_explain_v1", user_id):
        return None
        
    templates = EXPLANATION_TEMPLATES.get(event_type)
    if not templates:
        return None
        
    # Select Template
    text = random.choice(templates)
    
    # Log (Observability)
    try:
        db.log_event(user_id, "EXPLANATION_SHOWN", {
            "type": event_type,
            "flag": "phase7_explain_v1",
            "text": text
        })
    except Exception as e:
        logger.error(f"Failed to log explanation: {e}")
        
    return text
