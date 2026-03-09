import sys
import os
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import text, select, delete
import subprocess

sys.path.append(os.getcwd())

from backend.database import get_sync_db
from backend.models import LocalDish, MenuTemplate, MenuFeedback, FeatureFlag, OptimizationLog, DishReviewQueue

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("VERIFY")

def cleanup(session):
    logger.info("🧹 Cleaning up test data...")
    session.execute(delete(MenuFeedback).where(MenuFeedback.rating.like('TEST%'))) # Hack: Use user_id filter ideally
    # But user_id is integer.
    # We will use specific user_id -999 for tests.
    session.execute(delete(MenuFeedback).where(MenuFeedback.user_id == -999))
    session.execute(delete(DishReviewQueue).where(DishReviewQueue.reason == "TEST_REASON"))
    
    # Delete dishes
    session.execute(delete(LocalDish).where(LocalDish.name_uz.in_(['TEST_DISH_BAD', 'TEST_DISH_GOOD'])))
    
    # Delete User
    from backend.models import User
    session.execute(delete(User).where(User.telegram_id == -999))
    
    # Delete Template
    session.execute(delete(MenuTemplate).where(MenuTemplate.profile_key == "TEST_PROFILE"))
    
    session.commit()

def create_test_data(session):
    logger.info("🌱 Seeding test data...")
    
    # 1. Flag ON
    flag = session.get(FeatureFlag, 'optimization_v1')
    if not flag:
        flag = FeatureFlag(key='optimization_v1', enabled=True)
        session.add(flag)
    else:
        flag.enabled = True
    
    # 2. Dishes
    bad_dish = LocalDish(
        name_uz="TEST_DISH_BAD", meal_type="lunch", portion_type="plate", 
        total_kcal=500, protein_g=20, fat_g=20, carbs_g=50, 
        goal_tag="maintenance", variant="normal", is_active=True, featured=False
    )
    good_dish = LocalDish(
        name_uz="TEST_DISH_GOOD", meal_type="dinner", portion_type="plate", 
        total_kcal=500, protein_g=20, fat_g=20, carbs_g=50, 
        goal_tag="maintenance", variant="normal", is_active=True, featured=False
    )
    session.add(bad_dish)
    session.add(good_dish)
    session.commit() # Get IDs
    
    # 3. Menu Template
    # We need a template where Day 1 has BAD dish and Day 2 has GOOD dish
    menu_data = [
        {
            "day": 1,
            "meals": {
                "lunch": {"title": "TEST_DISH_BAD", "calories": 500}
            }
        },
        {
            "day": 2,
            "meals": {
                "dinner": {"title": "TEST_DISH_GOOD", "calories": 500}
            }
        }
    ]
    
    tmpl = MenuTemplate(
        profile_key="TEST_PROFILE",
        menu_json=json.dumps(menu_data),
        shopping_list_json="[]"
    )
    session.add(tmpl)
    session.commit()
    
    # Create User
    from backend.models import User
    u = session.query(User).filter(User.telegram_id == -999).first()
    if not u:
        u = User(telegram_id=-999, username="test_opt_user")
        session.add(u)
        session.commit()

    # 4. Feedback
    # 10 BAD votes for Day 1 (Dish Bad)
    for i in range(10):
        session.add(MenuFeedback(
            user_id=-999, menu_template_id=tmpl.id, day_index=1, rating="bad", 
            created_at=datetime.utcnow()
        ))
    
    # 10 GOOD votes for Day 2 (Dish Good)
    for i in range(15): # > 10 min votes
        session.add(MenuFeedback(
            user_id=-999, menu_template_id=tmpl.id, day_index=2, rating="good",
            created_at=datetime.utcnow()
        ))
        
    session.commit()
    return bad_dish.id, good_dish.id

def verify():
    with get_sync_db() as session:
        cleanup(session)
        bad_id, good_id = create_test_data(session)
    
    # Run Script
    logger.info("🚀 Running weekly_optimization.py --apply...")
    cmd = ["python3", "scripts/weekly_optimization.py", "--apply"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        logger.error("Script failed!")
        return

    # Check Results
    with get_sync_db() as session:
        bad_dish = session.get(LocalDish, bad_id)
        good_dish = session.get(LocalDish, good_id)
        
        # Check Bad Dish (Should be disabled or downgraded)
        # 10/10 bad = 100% bad rate >= 60% -> DISABLE
        if not bad_dish.is_active:
            logger.info("✅ PASS: TEST_DISH_BAD is disabled.")
            
            # Check Log
            log = session.execute(
                select(OptimizationLog).where(OptimizationLog.entity_id==bad_id, OptimizationLog.action=='DISABLE')
            ).scalar()
            if log:
                logger.info(f"✅ PASS: Found OptimizationLog DISABLE for {bad_id}.")
            else:
                logger.error("❌ FAIL: No OptimizationLog found.")
        else:
             logger.error(f"❌ FAIL: TEST_DISH_BAD is still active! (Rate: 100% Bad)")
             
        # Check Good Dish (Should be featured)
        # 15/15 good = 100% good rate >= 70% -> FEATURE
        if good_dish.featured:
            logger.info("✅ PASS: TEST_DISH_GOOD is featured.")
        else:
            logger.error("❌ FAIL: TEST_DISH_GOOD is NOT featured!")

        # Check Queue (Bad dish should be in queue)
        q = session.execute(
            select(DishReviewQueue).where(DishReviewQueue.dish_id==bad_id, DishReviewQueue.reason=='HIGH_BAD_RATE')
        ).scalar()
        if q:
             logger.info("✅ PASS: Bad dish found in Review Queue.")
        else:
             logger.error("❌ FAIL: Bad dish NOT in Review Queue.")

        # CLEANUP
        cleanup(session)

if __name__ == "__main__":
    verify()
