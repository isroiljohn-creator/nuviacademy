import argparse
import logging
from sqlalchemy import text
from backend.database import get_sync_db
from core.nutrition import lookup_usda_macros

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Recalc")

def recalc(apply=False):
    with get_sync_db() as session:
        # Fetch all dishes
        sql = text("""
            SELECT d.id, d.name_uz, d.total_kcal, d.protein_g, d.fat_g, d.carbs_g
            FROM local_dishes d
            WHERE d.is_active = TRUE
        """)
        dishes = session.execute(sql).fetchall()
        
        total_ingredients = 0
        matched_ingredients = 0
        failed_ingredients = {}

        logger.info(f"Processing {len(dishes)} dishes...")

        for dish_id, name, old_kcal, old_p, old_f, old_c in dishes:
            # Fetch ingredients
            ing_sql = text("""
                SELECT ingredient_name_uz, grams, fdc_id
                FROM local_dish_ingredients
                WHERE dish_id = :id
            """)
            ingredients = session.execute(ing_sql, {"id": dish_id}).fetchall()
            
            new_kcal, new_p, new_f, new_c = 0.0, 0.0, 0.0, 0.0
            all_matched = True

            for iname, grams, fdc_id in ingredients:
                total_ingredients += 1
                # Try lookup
                # We'll use lookup_usda_macros which handles aliases and fuzzy
                res = lookup_usda_macros(iname, iname)
                
                if res:
                    matched_ingredients += 1
                    ratio = grams / 100.0
                    new_kcal += res['kcal_100g'] * ratio
                    new_p += res['protein_100g'] * ratio
                    new_f += res['fat_100g'] * ratio
                    new_c += res['carbs_100g'] * ratio
                else:
                    all_matched = False
                    failed_ingredients[iname] = failed_ingredients.get(iname, 0) + 1
            
            if all_matched:
                diff_kcal = abs(new_kcal - old_kcal)
                if diff_kcal > 10: # Significance threshold
                    logger.info(f"Dish '{name}': Macros diff found. Old: {old_kcal}, New: {int(new_kcal)}")
                    if apply:
                        session.execute(text("""
                            UPDATE local_dishes 
                            SET total_kcal = :kcal, protein_g = :p, fat_g = :f, carbs_g = :c
                            WHERE id = :id
                        """), {
                            "kcal": int(new_kcal),
                            "p": round(new_p, 1),
                            "f": round(new_f, 1),
                            "c": round(new_c, 1),
                            "id": dish_id
                        })
                        session.commit()
            else:
                logger.debug(f"Dish '{name}': Some ingredients not matched, skipping recalc.")

        # Final Report
        match_rate = (matched_ingredients / total_ingredients * 100) if total_ingredients > 0 else 0
        logger.info(f"--- Recalc Report ---")
        logger.info(f"MATCH_RATE: {match_rate:.1f}%")
        
        top_failed = sorted(failed_ingredients.items(), key=lambda x: x[1], reverse=True)[:10]
        if top_failed:
            logger.info(f"Top FAILED_INGREDIENTS:")
            for item, count in top_failed:
                logger.info(f" - {item}: {count} times")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply updates to database")
    args = parser.parse_args()
    
    recalc(apply=args.apply)
