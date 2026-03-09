import json
import os
import sys
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import Session
from core.db import get_sync_db
from backend.models import LocalDish, LocalDishIngredient

DATA_FILE = "data/local_dishes_seed_real_200.json"

def validate_dish(d):
    # Macros check
    if any(x < 0 for x in [d['total_kcal'], d['protein_g'], d['fat_g'], d['carbs_g']]):
        raise ValueError(f"Negative macros in {d['name_uz']}")
    
    # Kcal range
    if d['meal_type'] == 'snack':
        if not (50 <= d['total_kcal'] <= 600): # relaxed slightly
             raise ValueError(f"Snack kcal out of range: {d['total_kcal']}")
    else:
        if not (50 <= d['total_kcal'] <= 1500): # relaxed slightly
             raise ValueError(f"Meal kcal out of range: {d['total_kcal']}")

    # Ingredients count
    if not (1 <= len(d['ingredients']) <= 15):
        raise ValueError(f"Ingredients count invalid: {len(d['ingredients'])}")
        
    for ing in d['ingredients']:
        if ing['grams'] <= 0:
             raise ValueError(f"Ingredient grams invalid: {ing['grams']}")

def seed():
    if not os.path.exists(DATA_FILE):
        print(f"File not found: {DATA_FILE}")
        sys.exit(1)
        
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
        
    print(f"Loaded {len(dishes)} dishes from JSON.")
    
    success_count = 0
    error_count = 0
    
    # We use one session but commit individually
    with get_sync_db() as session:
        for idx, d in enumerate(dishes):
            try:
                validate_dish(d)
                
                # Check for existing
                stmt = select(LocalDish).where(
                    and_(
                        LocalDish.name_uz == d['name_uz'],
                        LocalDish.meal_type == d['meal_type'],
                        LocalDish.variant == d['variant'],
                        LocalDish.portion_type == d['portion_type'],
                        LocalDish.goal_tag == d['goal_tag']
                    )
                )
                existing = session.execute(stmt).scalar_one_or_none()
                
                if existing:
                    dish = existing
                    # Update fields
                    dish.total_kcal = d['total_kcal']
                    dish.protein_g = d['protein_g']
                    dish.fat_g = d['fat_g']
                    dish.carbs_g = d['carbs_g']
                    dish.is_active = d['is_active']
                    # Clear ingredients
                    session.execute(delete(LocalDishIngredient).where(LocalDishIngredient.dish_id == dish.id))
                else:
                    dish = LocalDish(
                        name_uz=d['name_uz'],
                        meal_type=d['meal_type'],
                        portion_type=d['portion_type'],
                        total_kcal=d['total_kcal'],
                        protein_g=d['protein_g'],
                        fat_g=d['fat_g'],
                        carbs_g=d['carbs_g'],
                        goal_tag=d['goal_tag'],
                        variant=d['variant'],
                        is_active=d['is_active'],
                        featured=False
                    )
                    session.add(dish)
                    session.flush() # get ID
                
                # Add ingredients
                for ing in d['ingredients']:
                    db_ing = LocalDishIngredient(
                        dish_id=dish.id,
                        ingredient_name_uz=ing['name_uz'],
                        grams=ing['grams'],
                        fdc_id=ing.get('fdc_id')
                    )
                    session.add(db_ing)
                
                session.commit()
                success_count += 1
                # print(f"Encoded: {d['name_uz']}")
                
            except Exception as e:
                session.rollback()
                print(f"❌ Error processing {d.get('name_uz', 'UNKNOWN')}: {e}")
                error_count += 1
                sys.exit(1) # Stop immediately as requested

    print(f"\n✅ Seed complete. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    seed()
