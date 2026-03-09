import json
import random
import logging
from datetime import datetime
from sqlalchemy import text
from backend.database import get_sync_db
from core.flags import is_flag_enabled

logger = logging.getLogger("MenuAssembly")

def assemble_menu_7day(user_data, kcal_target):
    """
    Assembles a 7-day menu from local_dishes.
    Target: kcal_target ± 5% daily.
    Returns: JSON string in current MenuTemplate format.
    """
    user_id = user_data.get("telegram_id")
    goal = user_data.get("goal", "maintenance")
    variant = user_data.get("variant") 
    
    # Map goal to default variant if not explicitly provided
    if not variant:
        if goal == "weight_loss":
            variant = "diet"
        elif goal == "muscle_gain":
            variant = "athlete"
        else:
            variant = "normal"
    
    # [ADAPTATION ENGINE V1]
    adaptation_events = []
    if user_id:
        try:
            from core.adaptation import apply_menu_adaptation
            adapted_kcal, adapted_variant = apply_menu_adaptation(user_data, kcal_target, user_id)
            if adapted_kcal != kcal_target:
                 logger.info(f"Adaptation: Kcal {kcal_target} -> {adapted_kcal}")
                 kcal_target = adapted_kcal
                 adaptation_events.append("menu_kcal_adjusted")
            if adapted_variant:
                 logger.info(f"Adaptation: Variant {variant} -> {adapted_variant}")
                 variant = adapted_variant
                 adaptation_events.append("menu_variant_changed")
        except ImportError:
             pass # Safe fallback
        except Exception as e:
             logger.error(f"Adaptation Error: {e}")

    if not is_flag_enabled("db_menu_assembly", user_id):
        return None # Signal to use legacy AI generator

    # Band kcal for profile key (e.g. 1450 if target is 1400-1500)
    kcal_band = (kcal_target // 100) * 100
    profile_key = f"menu_v3_{goal}_{kcal_band}_{variant}"

    # 1. Check Cache
    with get_sync_db() as session:
        from backend.models import MenuTemplate
        cached = session.query(MenuTemplate).filter(MenuTemplate.profile_key == profile_key).first()
        if cached:
            logger.info(f"CACHE_HIT: profile_key={profile_key}")
            return cached.menu_json

    # 2. Fetch Dishes
    dishes_by_type = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "snack": []
    }
    
    with get_sync_db() as session:
        sql = text("""
            SELECT d.id, d.name_uz, d.meal_type, d.total_kcal, d.portion_type,
                   array_agg(i.ingredient_name_uz || ' (' || i.grams || 'g)') as ingredients
            FROM local_dishes d
            LEFT JOIN local_dish_ingredients i ON d.id = i.dish_id
            WHERE d.goal_tag = :goal AND d.variant = :variant AND d.is_active = TRUE
            GROUP BY d.id
        """)
        rows = session.execute(sql, {"goal": goal, "variant": variant}).fetchall()
        
        for r in rows:
            dishes_by_type[r[2]].append({
                "id": r[0],
                "title": r[1],
                "kcal": r[3],
                "portion": r[4],
                "items": r[5] if r[5][0] is not None else []
            })

    # 3. Assemble Days
    menu_days = []
    day_names_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    
    # Check if we have enough dishes
    for mtype, items in dishes_by_type.items():
        if len(items) < 3: # Arbitrary "enough" threshold
            logger.warning(f"INSUFFICIENT_DATA: type={mtype} goal={goal} count={len(items)}")
            logger.info("MENU_SOURCE=AI is_fallback=true fallback_reason=insufficient_data")
            return None # Fallback to AI

    for i in range(7):
        # Basic assembly logic: try to hit target kcal
        # We'll use a simple greedy approach with randomization
        day_meals = {}
        day_total_kcal = 0
        
        # Select one of each
        for mtype in ["breakfast", "lunch", "dinner", "snack"]:
            candidates = dishes_by_type[mtype]
            random.shuffle(candidates)
            
            best_dish = candidates[0]
            # Ideally would loop to find best fit for remaining kcal budget, 
            # but with limited samples we just pick one.
            day_meals[mtype] = {
                "title": best_dish["title"],
                "calories": best_dish["kcal"],
                "items": best_dish["items"],
                "recipe": "Tayyorlash usuli bazada mavjud emas.", # Placeholder or fetch from DB
                "steps": ["Bazada qidirilmoqda..."]
            }
            day_total_kcal += best_dish["kcal"]

        menu_days.append({
            "day": i + 1,
            "day_name": day_names_uz[i],
            "meals": day_meals,
            "total_calories": day_total_kcal
        })

    # 4. Aggregate Shopping List
    shopping_list = {"Barcha mahsulotlar": []}
    all_items = set()
    for day in menu_days:
        for mtype, meal in day["meals"].items():
            for itm in meal["items"]:
                all_items.add(itm)
    shopping_list["Barcha mahsulotlar"] = sorted(list(all_items))

    assemble_obj = {"menu": menu_days, "shopping_list": shopping_list}
    
    # [PHASE 7.1] Explain Engine
    if adaptation_events:
        try:
            from core.explain import get_explanation
            # Prioritize the last event or any? Let's take the first one or logic.
            # Usually variant change is more impactful than kcal. 
            # If both, maybe show one? 
            # Let's pick 'menu_variant_changed' if present, else 'menu_kcal_adjusted'.
            evt = "menu_variant_changed" if "menu_variant_changed" in adaptation_events else adaptation_events[0]
            
            exp = get_explanation(evt, {"user_id": user_id})
            if exp:
                assemble_obj["explanation"] = exp
        except ImportError: pass
        except Exception as e: logger.error(f"Explain Error: {e}")

    final_json = json.dumps(assemble_obj, ensure_ascii=False)

    # 5. Persist to MenuTemplate
    with get_sync_db() as session:
        new_template = MenuTemplate(
            profile_key=profile_key,
            menu_json=final_json,
            shopping_list_json=json.dumps(shopping_list, ensure_ascii=False)
        )
        session.add(new_template)
        session.commit()

    logger.info("MENU_SOURCE=LOCAL")
    return final_json

def get_swap_options(user_data, meal_type, target_kcal, current_dish_id=None, limit=3):
    """
    Finds alternative dishes for a specific meal slot.
    Logic: Same meal_type, same variant/goal (if avail), kcal within +/- 15%.
    """
    goal = user_data.get("goal", "maintenance")
    variant = user_data.get("variant") 
    if not variant:
        if goal == "weight_loss": variant = "diet"
        elif goal == "muscle_gain": variant = "athlete"
        else: variant = "normal"

    min_kcal = target_kcal * 0.85
    max_kcal = target_kcal * 1.15

    with get_sync_db() as session:
        # Try strict match first
        sql_strict = text("""
            SELECT id, name_uz, total_kcal, portion_type 
            FROM local_dishes 
            WHERE meal_type = :mtype 
              AND goal_tag = :goal 
              AND variant = :variant 
              AND total_kcal BETWEEN :min_k AND :max_k
              AND is_active = TRUE
              AND id != :curr_id
            LIMIT :limit
        """)
        rows = session.execute(sql_strict, {
            "mtype": meal_type, "goal": goal, "variant": variant,
            "min_k": min_kcal, "max_k": max_kcal, "curr_id": current_dish_id or -1,
            "limit": limit
        }).fetchall()
        
        # Fallback to loose match (ignore goal/variant, just calories & type)
        if len(rows) < limit:
            needed = limit - len(rows)
            exclude_ids = [r[0] for r in rows]
            if current_dish_id: exclude_ids.append(current_dish_id)
            
            sql_loose = text("""
                SELECT id, name_uz, total_kcal, portion_type 
                FROM local_dishes 
                WHERE meal_type = :mtype 
                  AND total_kcal BETWEEN :min_k AND :max_k
                  AND is_active = TRUE
                  AND id NOT IN :exclude
                LIMIT :limit
            """)
            rows_loose = session.execute(sql_loose, {
                "mtype": meal_type, 
                "min_k": min_kcal, "max_k": max_kcal, 
                "exclude": tuple(exclude_ids) if exclude_ids else (-1,),
                "limit": needed
            }).fetchall()
            rows.extend(rows_loose)
            
    return [{"id": r[0], "title": r[1], "calories": r[2]} for r in rows]
