import re
import logging
from backend.database import get_sync_db
from sqlalchemy import text
from core.flags import is_flag_enabled

logger = logging.getLogger("Nutrition")

# Uzbek to English Mapping (Minimal for POC as requested)
UZ_EN_MAP = {
    # Ingredients
    "tuxum": "egg",
    "guruch": "rice",
    "tovuq": "chicken",
    "sut": "milk",
    "qatiq": "yogurt",
    "kefir": "kefir",
    "bodring": "cucumber",
    "pomidor": "tomato",
    "karam": "cabbage",
    "sabzi": "carrot",
    "piyoz": "onion",
    "grechka": "buckwheat",
    "mol goshti": "beef",
    "mol go'shti": "beef",
    "baliq": "fish",
    "olma": "apple",
    "banan": "banana",
    "non": "bread",
    "pishloq": "cheese",
    "yog'": "oil",
    "zaytun moyi": "olive oil",
    "shakar": "sugar",
    "tuz": "salt",
    "kartoshka": "potato",
    "sarimsoq": "garlic",
    "qalampir": "pepper",
    "go'sht": "meat",
    "un": "flour",
    "suv": "water",
    
    # Common Dishes (for mapping or basic identification)
    "osh": "pilaf",
    "palov": "pilaf",
    "shurva": "soup",
    "sho'rva": "soup",
    "manti": "manti",
    "somsa": "samosa",
    "lagmon": "noodles",
    "dimlama": "stew",
    "shashlik": "kebab"
}

# Unit to Grams Conversion Rules
UNIT_GRAMS = {
    "dona": {
        "egg": 60,
        "apple": 180,
        "banana": 120,
        "somsa": 100,
        "manti": 50,
        "default": 100
    },
    "osh qoshiq": 15,
    "choy qoshiq": 5,
    "stakan": 200,
    "kosa": 300,
    "piyola": 150,
    "g": 1,
    "gramm": 1,
    "ml": 1  # Assume 1ml ≈ 1g for liquids
}

def normalize_ingredient(ing_str):
    """
    Parses ingredient string like "Tuxum (2 dona)" or "Guruch (100g)".
    Returns dict with name_uz, name_en, qty, unit, grams_est.
    """
    ing_str = ing_str.lower().strip()
    
    # regex to match "name (qty unit)" or "name qty unit"
    pattern = r"([a-z'‘\s]+)(?:\(?([\d\.,]+)\s*([a-z\s]+)\)?)?"
    match = re.match(pattern, ing_str)
    
    if not match:
        return None
        
    name_uz = match.group(1).strip()
    qty_str = match.group(2)
    unit = match.group(3).strip() if match.group(3) else "g"
    
    # Parse quantity
    try:
        qty = float(qty_str.replace(',', '.')) if qty_str else 1.0
    except ValueError:
        qty = 1.0
        
    name_en = UZ_EN_MAP.get(name_uz, name_uz)
    
    # Estimate grams
    grams_est = 0
    if unit in UNIT_GRAMS:
        conv = UNIT_GRAMS[unit]
        if isinstance(conv, dict):
            grams_est = conv.get(name_en, conv.get("default", 100)) * qty
        else:
            grams_est = conv * qty
    else:
        # Fallback if unit not recognized, assume it might be 'g' or something else
        grams_est = 100 * qty if "dona" not in unit else 60 * qty
    
    return {
        "raw": ing_str,
        "name_uz": name_uz,
        "name_en": name_en,
        "qty": qty,
        "unit": unit,
        "grams_est": int(grams_est)
    }

def lookup_usda_macros(name_uz, name_en, user_id=None):
    """
    Query usda.food_macros for the best match.
    Priority (V2):
    1. local_dishes (exact name_uz match)
    2. usda.uz_food_alias (exact name_uz match)
    3. usda.food_macros (fuzzy name_en match)
    """
    v2_enabled = is_flag_enabled("calorie_engine_v2", user_id) if user_id else False

    with get_sync_db() as session:
        # 1. Local Dishes Lookup (Priority 1 if V2 enabled)
        if v2_enabled:
            dish_sql = text("""
                SELECT total_kcal, protein_g, fat_g, carbs_g
                FROM local_dishes
                WHERE name_uz = :uz_name AND is_active = TRUE
                LIMIT 1
            """)
            dish_res = session.execute(dish_sql, {"uz_name": name_uz}).fetchone()
            if dish_res:
                return {
                    "source": "LOCAL",
                    "match_source": "DISH",
                    "kcal_100g": float(dish_res[0]), # For dishes, we treat this as total if it's a fixed portion dish
                    "protein_100g": float(dish_res[1]),
                    "fat_100g": float(dish_res[2]),
                    "carbs_100g": float(dish_res[3]),
                    "is_dish": True
                }

        # 2. Alias Lookup (Priority 2 or 1 if V1) - Skip if USDA schema not initialized
        try:
            alias_sql = text("""
                SELECT f.kcal_100g, f.protein_100g, f.fat_100g, f.carbs_100g
                FROM usda.uz_food_alias a
                JOIN usda.food_macros f ON a.fdc_id = f.fdc_id
                WHERE a.uz_name = :uz_name
            """)
            alias_res = session.execute(alias_sql, {"uz_name": name_uz}).fetchone()
            
            if alias_res:
                return {
                    "source": "USDA",
                    "match_source": "ALIAS",
                    "kcal_100g": float(alias_res[0]),
                    "protein_100g": float(alias_res[1]),
                    "fat_100g": float(alias_res[2]),
                    "carbs_100g": float(alias_res[3])
                }
        except Exception:
            # USDA schema not initialized, skip
            pass

        # 3. Fuzzy Lookup
        fuzzy_sql = text("""
            SELECT kcal_100g, protein_g, fat_g, carbs_g, description
            FROM usda.food_macros
            WHERE description ILIKE :name
            ORDER BY kcal_100g DESC NULLS LAST
            LIMIT 1
        """)
        # Note: food_macros view uses kcal_100g, protein_100g etc, but let's check view definition.
        # Viewed usda_schema.sql: kcal_100g, protein_100g, fat_100g, carbs_100g.
        fuzzy_sql = text("""
            SELECT kcal_100g, protein_100g, fat_100g, carbs_100g, description
            FROM usda.food_macros
            WHERE description ILIKE :name
            ORDER BY kcal_100g DESC NULLS LAST
            LIMIT 1
        """)
        fuzzy_res = session.execute(fuzzy_sql, {"name": f"%{name_en}%"}).fetchone()
        
        if fuzzy_res:
            return {
                "source": "USDA",
                "match_source": "FUZZY",
                "kcal_100g": float(fuzzy_res[0]),
                "protein_100g": float(fuzzy_res[1]),
                "fat_100g": float(fuzzy_res[2]),
                "carbs_100g": float(fuzzy_res[3]),
                "matched_key": fuzzy_res[4]
            }
            
    return None

def calculate_macros(usda_data, grams_est):
    """
    Calculate absolute macros based on estimated grams.
    If 'is_dish' is True, we use the value as a per-portion total (fixed).
    """
    if not usda_data:
        return None
        
    if usda_data.get("is_dish"):
        return {
            "kcal": int(usda_data["kcal_100g"]),
            "protein": round(usda_data["protein_100g"], 1),
            "fat": round(usda_data["fat_100g"], 1),
            "carbs": round(usda_data["carbs_100g"], 1)
        }

    ratio = grams_est / 100.0
    return {
        "kcal": round(usda_data["kcal_100g"] * ratio),
        "protein": round(usda_data["protein_100g"] * ratio, 1),
        "fat": round(usda_data["fat_100g"] * ratio, 1),
        "carbs": round(usda_data["carbs_100g"] * ratio, 1)
    }

def process_menu_nutrition(menu_json_str):
    """
    Post-processor for the AI menu JSON.
    Updates meal calories and adds day summaries.
    """
    import json
    try:
        menu_days = json.loads(menu_json_str)
    except Exception as e:
        logger.error(f"Failed to parse menu JSON for nutrition processing: {e}")
        return menu_json_str

    total_stats = {
        "total_calories": 0,
        "matches": 0,
        "failures": [],
        "total_ingredients": 0,
        "sources": {"ALIAS": 0, "FUZZY": 0}
    }

    for day in menu_days:
        day_total_kcal = 0
        day_protein = 0
        day_fat = 0
        day_carbs = 0
        
        meals = day.get("meals", {})
        for meal_type, meal in meals.items():
            if not isinstance(meal, dict):
                continue
                
            ingredients = meal.get("items", [])
            meal_kcal = 0
            meal_protein = 0
            meal_fat = 0
            meal_carbs = 0
            
            meal_matched = False
            
            for ing_str in ingredients:
                total_stats["total_ingredients"] += 1
                norm = normalize_ingredient(ing_str)
                if norm:
                    usda = lookup_usda_macros(norm["name_uz"], norm["name_en"])
                    if usda:
                        macros = calculate_macros(usda, norm["grams_est"])
                        if macros:
                            meal_kcal += macros["kcal"]
                            meal_protein += macros["protein"]
                            meal_fat += macros["fat"]
                            meal_carbs += macros["carbs"]
                            total_stats["matches"] += 1
                            total_stats["sources"][usda["source"]] += 1
                            meal_matched = True
                            continue
                
                # If we reach here, lookup failed
                total_stats["failures"].append(ing_str)

            # If we had at least one USDA match, use our calculated kcal
            # Otherwise, keep original AI estimate as fallback
            if meal_matched:
                meal["calories"] = int(meal_kcal)
                meal["macros"] = {
                    "protein": round(meal_protein, 1),
                    "fat": round(meal_fat, 1),
                    "carbs": round(meal_carbs, 1)
                }
            
            day_total_kcal += meal.get("calories", 0)
            day_protein += meal.get("macros", {}).get("protein", 0) if "macros" in meal else 0
            day_fat += meal.get("macros", {}).get("fat", 0) if "macros" in meal else 0
            day_carbs += meal.get("macros", {}).get("carbs", 0) if "macros" in meal else 0

        day["total_calories"] = int(day_total_kcal)
        day["day_macros"] = {
            "protein_g": round(day_protein, 1),
            "fat_g": round(day_fat, 1),
            "carbs_g": round(day_carbs, 1)
        }
        total_stats["total_calories"] += day_total_kcal

    # Log results
    match_rate = (total_stats["matches"] / total_stats["total_ingredients"] * 100) if total_stats["total_ingredients"] > 0 else 0
    logger.info(f"MENU_KCAL_SOURCE={'USDA' if total_stats['matches'] > 0 else 'FALLBACK'} MATCH_RATE={match_rate:.1f}%")
    logger.info(f"SOURCES: ALIAS={total_stats['sources']['ALIAS']} FUZZY={total_stats['sources']['FUZZY']}")
    logger.info(f"TOTAL_KCAL={total_stats['total_calories']}")
    if total_stats["failures"]:
        logger.warning(f"FAILED_INGREDIENTS={total_stats['failures'][:10]}...")

    return json.dumps(menu_days, ensure_ascii=False)

def analyze_ingredients_list(ingredients, user_id=None):
    """
    Takes a list of ingredient strings (e.g. ['tuxum (2 dona)', 'osh (200g)'])
    Returns total macros and source statistics.
    """
    res = {
        "total_kcal": 0,
        "total_protein": 0,
        "total_fat": 0,
        "total_carbs": 0,
        "items": [],
        "match_count": 0,
        "source_dist": {"LOCAL": 0, "USDA": 0, "AI": 0},
        "match_sources": {"DISH": 0, "ALIAS": 0, "FUZZY": 0, "FALLBACK": 0}
    }
    
    failed_ingredients = []

    for ing_str in ingredients:
        norm = normalize_ingredient(ing_str)
        if norm:
            usda = lookup_usda_macros(norm["name_uz"], norm["name_en"], user_id=user_id)
            if usda:
                macros = calculate_macros(usda, norm["grams_est"])
                if macros:
                    res["total_kcal"] += macros["kcal"]
                    res["total_protein"] += macros["protein"]
                    res["total_fat"] += macros["fat"]
                    res["total_carbs"] += macros["carbs"]
                    res["match_count"] += 1
                    
                    source = usda.get("source", "USDA")
                    match_source = usda.get("match_source", "UNKNOWN")
                    
                    res["source_dist"][source] = res["source_dist"].get(source, 0) + 1
                    res["match_sources"][match_source] = res["match_sources"].get(match_source, 0) + 1
                    
                    res["items"].append({
                        "name": norm["name_uz"],
                        "qty": norm["qty"],
                        "unit": norm["unit"],
                        "kcal": macros["kcal"],
                        "source": source,
                        "match_source": match_source
                    })
                    continue
        
        # Fallback/Fail if not found in USDA or normalization failed
        failed_ingredients.append(ing_str)
        res["items"].append({
            "name": ing_str,
            "kcal": 0,
            "source": "AI", # This will be estimated by AI caller
            "match_source": "FALLBACK"
        })
        res["source_dist"]["AI"] += 1
        res["match_sources"]["FALLBACK"] += 1
        
    # Log Match Rate
    if ingredients:
        match_rate = (res["match_count"] / len(ingredients)) * 100
        logger.info(f"CALORIE_ENGINE_STATS: user={user_id} match_rate={match_rate:.1f}% dist={res['source_dist']}")
        
        from core.db import db
        db.log_admin_event(
            event_type="CALORIE_ANALYSIS",
            user_id=user_id,
            success=True,
            meta={
                "match_rate": round(match_rate, 1),
                "source_dist": res["source_dist"],
                "match_sources": res["match_sources"],
                "item_count": len(ingredients)
            }
        )
    
    return res

def format_nutrition_result(analysis_res, lang="uz"):
    """Formats the analysis result for bot output."""
    dist = analysis_res.get("source_dist", {})
    if dist.get("AI", 0) > 0:
        source_label = "(AI+)"
    elif dist.get("LOCAL", 0) > 0 and dist.get("USDA", 0) == 0:
        source_label = "(BAZA)"
    else:
        source_label = "(USDA)"

    if lang == 'ru':
        text = f"🍽 <b>Анализ Калорий {source_label}</b>\n\n"
        for item in analysis_res["items"]:
            if item["source"] != "UNKNOWN":
                qstr = f"({item.get('qty', '')} {item.get('unit', '')})" if item.get('qty') else ""
                text += f"▫️ {item['name'].capitalize()} {qstr}: {item['kcal']} ккал\n"
            else:
                text += f"▫️ {item['name']}: (расчет AI)\n"
        
        text += f"\n🔥 <b>Всего: {round(analysis_res['total_kcal'])} ккал</b>\n"
        text += f"📊 <b>БЖУ:</b> {analysis_res['total_protein']}г / {analysis_res['total_fat']}г / {analysis_res['total_carbs']}г"
    else:
        text = f"🍽 <b>Kaloriya Tahlili {source_label}</b>\n\n"
        for item in analysis_res["items"]:
            if item["source"] != "UNKNOWN":
                qstr = f"({item.get('qty', '')} {item.get('unit', '')})" if item.get('qty') else ""
                text += f"▫️ {item['name'].capitalize()} {qstr}: {item['kcal']} kkal\n"
            else:
                text += f"▫️ {item['name']}: (AI hisobi)\n"
        
        text += f"\n🔥 <b>Jami: {round(analysis_res['total_kcal'])} kkal</b>\n"
        text += f"📊 <b>BJU:</b> {analysis_res['total_protein']}g / {analysis_res['total_fat']}g / {analysis_res['total_carbs']}g"
        
    return text
