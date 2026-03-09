import sys
import os
import json
import logging
from sqlalchemy import select, func
from sqlalchemy.orm import Session
import math

sys.path.append(os.getcwd())

from backend.database import get_sync_db
from backend.models import LocalDish, DishReviewQueue, OptimizationLog
from scripts.weekly_optimization import get_dish_stats

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Curation")

def curate_dishes():
    logger.info("Starting Auto-Curation (Statistical Analysis)")
    
    with get_sync_db() as session:
        # 1. Get Stats (7 days)
        stats = get_dish_stats(session, days=7)
        
        # Filter: Min 5 votes for stat significance
        candidates = []
        for did, s in stats.items():
            if s['total'] >= 5:
                # Calculate scores
                bad_rate = s['bad'] / s['total']
                good_rate = s['good'] / s['total']
                candidates.append({
                    'id': did, 'bad_rate': bad_rate, 'good_rate': good_rate, 'total': s['total'], 'stats': s
                })
        
        if not candidates:
            logger.info("Not enough data for curation.")
            return

        total_candidates = len(candidates)
        logger.info(f"Analyzing {total_candidates} candidates with >=5 votes.")
        
        # Sort by Bad Rate DESC
        candidates.sort(key=lambda x: x['bad_rate'], reverse=True)
        
        # Bottom 5% (High Bad Rate)
        cutoff_bad = max(1, int(math.ceil(total_candidates * 0.05)))
        bottom_dishes = candidates[:cutoff_bad]
        
        for d in bottom_dishes:
            if d['bad_rate'] >= 0.35: # Min threshold to care
                reason = "STAT_BOTTOM_5_PERCENT"
                # Check Queue
                exists = session.execute(
                    select(DishReviewQueue).where(DishReviewQueue.dish_id==d['id'], DishReviewQueue.reason==reason, DishReviewQueue.status=='open')
                ).scalar()
                
                if not exists:
                    q = DishReviewQueue(dish_id=d['id'], reason=reason, metrics=d['stats'])
                    session.add(q)
                    logger.info(f"Flagged Dish {d['id']} (Bad Rate {d['bad_rate']:.2%}) for review.")

        # Sort by Good Rate DESC
        candidates.sort(key=lambda x: x['good_rate'], reverse=True)
        
        # Top 10% (High Good Rate)
        cutoff_good = max(1, int(math.ceil(total_candidates * 0.10)))
        top_dishes = candidates[:cutoff_good]
        
        for d in top_dishes:
            if d['good_rate'] >= 0.70: # Min threshold
                dish = session.get(LocalDish, d['id'])
                if dish and not dish.featured:
                    dish.featured = True
                    # Log
                    log = OptimizationLog(
                        entity_type='dish', entity_id=d['id'], 
                        action='FEATURE_STAT', reason='TOP_10_PERCENT',
                        meta=json.dumps(d['stats'])
                    )
                    session.add(log)
                    logger.info(f"Promoted Dish {d['id']} (Good Rate {d['good_rate']:.2%}) to Featured.")

        session.commit()
        logger.info("Curation complete.")

if __name__ == "__main__":
    curate_dishes()
