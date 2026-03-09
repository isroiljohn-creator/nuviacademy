import json
import logging
from sqlalchemy import text
from backend.database import get_sync_db

logger = logging.getLogger("WorkoutSelector")

LEVEL_MAP = {
    "sedentary": "beginner",
    "light": "beginner",
    "moderate": "medium",
    "active": "advanced",
    "athlete": "advanced"
}

def get_day_name_uz(idx):
    days = {
        1: "Dushanba",
        2: "Seshanba",
        3: "Chorshanba",
        4: "Payshanba",
        5: "Juma",
        6: "Shanba",
        7: "Yakshanba"
    }
    return days.get(idx, f"{idx}-kun")

def select_workout_plan(user_data, apply_soft_mode=False):
    """
    Selects a workout plan from workout_plans based on user profile.
    Returns: dict with "source" and "schedule" or raises Exception for fallback.
    """
    goal_tag = user_data.get("goal", "health")
    activity = user_data.get("activity_level", "moderate")
    level = LEVEL_MAP.get(activity, "medium")
    
    # Place preference default 'uy'
    place = user_data.get("place", "uy") 

    # [ADAPTATION ENGINE V1]
    if not apply_soft_mode: # Only check if not already forced
        try:
            from core.adaptation import apply_workout_adaptation
            user_id = user_data.get("telegram_id")
            if user_id and apply_workout_adaptation(user_id):
                apply_soft_mode = True
                logger.info(f"Adaptation: forced soft_mode for {user_id}")
        except ImportError: pass
        except Exception as e:
            logger.error(f"Adaptation Error: {e}")

    with get_sync_db() as session:
        # Search strategy fallbacks
        search_params = [
            {"goal": goal_tag, "level": level, "place": place},
            {"goal": goal_tag, "level": level, "place": "ikkala"},
            {"goal": goal_tag, "level": "medium", "place": place},
            {"goal": goal_tag, "level": "medium", "place": "ikkala"},
            {"goal": goal_tag, "level": "beginner", "place": place},
            {"goal": goal_tag, "level": "beginner", "place": "ikkala"}
        ]
        
        plan_row = None
        for params in search_params:
            sql = text("""
                SELECT id, name, days_json
                FROM workout_plans
                WHERE goal_tag = :goal AND level = :level AND place = :place
                AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """)
            plan_row = session.execute(sql, params).fetchone()
            if plan_row:
                break
        
        if not plan_row:
            raise Exception(f"no_plan_match: goal={goal_tag} level={level} place={place}")

        plan_id, plan_name, days_json = plan_row
        
        if isinstance(days_json, str):
            days_data = json.loads(days_json)
        else:
            days_data = days_json

        full_plan = []
        for d_idx in range(1, 8):
            day_key = str(d_idx)
            day_content = days_data.get(day_key, "REST")
            
            is_rest = False
            if day_content == "REST":
                is_rest = True
            elif isinstance(day_content, dict) and day_content.get("is_rest_day"):
                is_rest = True
            
            day_struct = {
                "day_name": get_day_name_uz(d_idx),
                "is_rest_day": is_rest,
                "exercises": []
            }
            
            if not is_rest:
                exercises_refs = []
                if isinstance(day_content, list):
                    exercises_refs = day_content
                elif isinstance(day_content, dict) and "exercises" in day_content:
                    exercises_refs = day_content["exercises"]
                
                if not exercises_refs:
                    day_struct["is_rest_day"] = True # No exercises = rest day
                else:
                    for ex_ref in exercises_refs:
                        ex_id = ex_ref if isinstance(ex_ref, (int, str)) else ex_ref.get("id")
                        
                        ex_sql = text("""
                            SELECT name, video_url, muscle_group
                            FROM exercises WHERE id = :id OR name = :name
                        """)
                        # Support both ID and Name for backward compatibility as requested
                        ex_params = {"id": ex_id if str(ex_id).isdigit() else -1, "name": str(ex_id)}
                        ex_row = session.execute(ex_sql, ex_params).fetchone()
                        
                        if not ex_row:
                            raise Exception(f"missing_exercise: identifier={ex_id}")
                        
                        name, video_url, muscle_group = ex_row
                        
                        if not video_url:
                            raise Exception(f"missing_video_url: exercise={name}")
                        
                        sets_reps = "3 set x 12 marta"
                        rest_sec = 60
                        
                        if isinstance(ex_ref, dict):
                            sets_reps = ex_ref.get("sets_reps", sets_reps)
                            rest_sec = ex_ref.get("rest_sec", rest_sec)


                        if apply_soft_mode:
                            # Parse sets/reps if possible, simplified regex
                            import re
                            # "3 set x 12 marta" -> Reduce to "2 set x 10 marta"
                            match = re.match(r"(\d+)\s*set\s*x\s*(\d+)", sets_reps)
                            if match:
                                sets = int(match.group(1))
                                reps = int(match.group(2))
                                
                                new_sets = max(2, sets - 1)
                                new_reps = max(5, int(reps * 0.8))
                                sets_reps = f"{new_sets} set x {new_reps} marta (Yengil)"

                        day_struct["exercises"].append({
                            "title_uz": name,
                            "sets_reps": sets_reps,
                            "rest_sec": int(rest_sec),
                            "video_url": video_url,
                            "muscle_group": muscle_group
                        })
            
            full_plan.append(day_struct)

        result_obj = {
            "source": "DB",
            "schedule": full_plan,
            "is_soft_mode": apply_soft_mode
        }
        
        # [PHASE 7.1] Explain Engine
        if apply_soft_mode:
            try:
                from core.explain import get_explanation
                exp = get_explanation("workout_soft_mode_enabled", {"user_id": user_data.get("telegram_id")})
                if exp:
                    result_obj["explanation"] = exp
            except ImportError: pass
            except Exception as e: logger.error(f"Explain Error: {e}")
            
        return result_obj
