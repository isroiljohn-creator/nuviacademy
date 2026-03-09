import json
import logging
import sys
import os
from sqlalchemy import text
from backend.database import get_sync_db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Seeder")

def validate_dish(dish, session):
    """Strict validation for a dish and its ingredients."""
    name = dish.get('name_uz')
    mtype = dish.get('meal_type')
    kcal = dish.get('total_kcal')
    p = dish.get('protein_g')
    f = dish.get('fat_g')
    c = dish.get('carbs_g')
    ingredients = dish.get('ingredients', [])

    # Calorie ranges
    if mtype == 'snack':
        if not (50 <= kcal <= 350):
            raise ValueError(f"Dish '{name}': snack kcal {kcal} out of range (50-350)")
    elif mtype in ['breakfast', 'lunch', 'dinner']:
        if not (200 <= kcal <= 900):
            raise ValueError(f"Dish '{name}': {mtype} kcal {kcal} out of range (200-900)")
    else:
        raise ValueError(f"Dish '{name}': unknown meal_type '{mtype}'")

    # Macros
    if p < 0 or f < 0 or c < 0:
        raise ValueError(f"Dish '{name}': negative macros (P:{p}, F:{f}, C:{c})")

    # Ingredients
    if not (3 <= len(ingredients) <= 10):
        raise ValueError(f"Dish '{name}': ingredient count {len(ingredients)} out of range (3-10)")

    for ing in ingredients:
        iname = ing.get('name_uz')
        igrams = ing.get('grams')
        if not isinstance(igrams, int) or igrams <= 0:
            raise ValueError(f"Dish '{name}', Ingredient '{iname}': grams {igrams} must be INT > 0")
        
        fdc_id = ing.get('fdc_id')
        if fdc_id is not None:
            res = session.execute(text("SELECT fdc_id FROM usda.food WHERE fdc_id = :fdc_id"), {"fdc_id": fdc_id}).fetchone()
            if not res:
                raise ValueError(f"Dish '{name}': fdc_id {fdc_id} not found in usda.food")

def seed_dishes():
    seed_file = 'data/local_dishes_seed.json'
    if not os.path.exists(seed_file):
        logger.error(f"Seed file not found: {seed_file}")
        sys.exit(1)

    with open(seed_file, 'r', encoding='utf-8') as f:
        dishes = json.load(f)

    logger.info(f"Loaded {len(dishes)} dishes from seed file.")

    inserted = 0
    updated = 0

    with get_sync_db() as session:
        for dish in dishes:
            try:
                # 1. Validate (within transaction context for fdc_id check)
                validate_dish(dish, session)

                # 2. Transaction per dish
                session.execute(text("BEGIN"))
                
                # UPSERT local_dishes
                sql = text("""
                    INSERT INTO local_dishes (name_uz, meal_type, portion_type, total_kcal, protein_g, fat_g, carbs_g, goal_tag, variant, is_active)
                    VALUES (:name, :mtype, :portion, :kcal, :p, :f, :c, :goal, :variant, :active)
                    ON CONFLICT (name_uz, portion_type, variant) 
                    DO UPDATE SET 
                        total_kcal = EXCLUDED.total_kcal,
                        protein_g = EXCLUDED.protein_g,
                        fat_g = EXCLUDED.fat_g,
                        carbs_g = EXCLUDED.carbs_g,
                        is_active = EXCLUDED.is_active,
                        meal_type = EXCLUDED.meal_type,
                        goal_tag = EXCLUDED.goal_tag
                    RETURNING id, (xmin = 0) as is_new;
                """)
                # Note: (xmin = 0) is a trick to detect insert, but better to check rowcount or just count updates.
                # Actually, RETURNING will work.
                res = session.execute(sql, {
                    "name": dish['name_uz'],
                    "mtype": dish['meal_type'],
                    "portion": dish['portion_type'],
                    "kcal": dish['total_kcal'],
                    "p": dish['protein_g'],
                    "f": dish['fat_g'],
                    "c": dish['carbs_g'],
                    "goal": dish['goal_tag'],
                    "variant": dish['variant'],
                    "active": dish.get('is_active', True)
                }).fetchone()
                
                dish_id = res[0]
                # is_new detection is tricky with ON CONFLICT, we just increment based on logic or skip counts.
                # Let's assume if we got here, it's success.
                
                # Sync Ingredients
                session.execute(text("DELETE FROM local_dish_ingredients WHERE dish_id = :id"), {"id": dish_id})
                
                for ing in dish['ingredients']:
                    session.execute(text("""
                        INSERT INTO local_dish_ingredients (dish_id, ingredient_name_uz, grams, fdc_id)
                        VALUES (:id, :name, :grams, :fdc_id)
                    """), {
                        "id": dish_id,
                        "name": ing['name_uz'],
                        "grams": ing['grams'],
                        "fdc_id": ing.get('fdc_id')
                    })
                
                session.execute(text("COMMIT"))
                inserted += 1 # We'll just call it "processed" or "upserted"
                
            except Exception as e:
                session.execute(text("ROLLBACK"))
                logger.error(f"FAILED on dish '{dish.get('name_uz')}': {e}")
                logger.info("STOPPING seeder due to error.")
                sys.exit(1)

    logger.info(f"Seeding completed successfully. {inserted} dishes upserted.")

if __name__ == "__main__":
    seed_dishes()
