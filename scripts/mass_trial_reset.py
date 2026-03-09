import asyncio
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import update, text

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal, init_db
from backend.models import User, Subscription

async def mass_reset_to_trial():
    print("🚀 Starting Mass Reset to 14-Day Trial...")
    
    # Initialize DB (ensure tables exist)
    await init_db()
    
    async with SessionLocal() as db:
        try:
            # 1. Calculate trial end date
            trial_end = datetime.utcnow() + timedelta(days=14)
            trial_start_str = datetime.utcnow().strftime("%Y-%m-%d")
            
            # 2. Update all users
            user_update_stmt = (
                update(User)
                .values(
                    plan_type="trial",
                    is_premium=True,
                    premium_until=trial_end,
                    trial_start=trial_start_str,
                    trial_used=1
                )
            )
            user_result = await db.execute(user_update_stmt)
            users_count = user_result.rowcount
            
            # 3. Deactivate all direct subscriptions
            sub_update_stmt = (
                update(Subscription)
                .where(Subscription.is_active == True)
                .values(is_active=False)
            )
            sub_result = await db.execute(sub_update_stmt)
            subs_deactivated = sub_result.rowcount
            
            # 4. Commit changes
            await db.commit()
            
            print(f"✅ Successfully updated {users_count} users to 14-day trial.")
            print(f"✅ Deactivated {subs_deactivated} active subscriptions.")
            print(f"📅 New expiry date for all: {trial_end.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error during update: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(mass_reset_to_trial())
