import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.db import db
from backend.database import get_sync_db
from backend.models import User, ActivityLog
from core.utils import get_referrer_id_from_code

def recover_missing_referrals():
    print("🔍 Starting Referral Recovery Scan...")
    
    with get_sync_db() as session:
        # 1. Get all recent "message" activity logs that might be /start commands
        # We look for content starting with "/start "
        logs = session.query(ActivityLog).filter(
            ActivityLog.type == 'message',
            ActivityLog.payload.like('/start r%')
        ).all()
        
        print(f"📄 Found {len(logs)} potential referral start commands in logs.")
        
        recovered_count = 0
        
        for log in logs:
            try:
                # Parse command: "/start r123456"
                command = log.payload.strip()
                parts = command.split()
                if len(parts) < 2: continue
                
                code = parts[1]
                referrer_id_raw = get_referrer_id_from_code(code)
                
                if not referrer_id_raw:
                    continue
                    
                # User who sent the command (The invitee)
                # Note: ActivityLog stores user_id as PK, not Telegram ID.
                # However, our log_activity implementation in db.py takes telegram_id but stores PK.
                # So log.user_id is the PK.
                
                invitee = session.query(User).filter(User.id == log.user_id).first()
                if not invitee: continue
                
                # Check if invitee already has a referrer
                if invitee.referrer_id:
                    # Already has referrer, skip
                    continue
                    
                # Find Referrer User (The inviter)
                referrer = session.query(User).filter(User.telegram_id == referrer_id_raw).first()
                if not referrer: continue
                
                # Self-referral check
                if referrer.id == invitee.id:
                    continue
                    
                print(f"🛠 Fixing: User {invitee.telegram_id} (ID: {invitee.id}) -> Referrer {referrer.telegram_id} (ID: {referrer.id})")
                
                # 2. Update Referrer Link
                invitee.referrer_id = referrer.id
                
                # 3. Add Points to Referrer
                # We add +1 point directly
                referrer.points = (referrer.points or 0) + 1
                referrer.yasha_points = (referrer.yasha_points or 0) + 1
                
                # 4. Notify Referrer (Optional, maybe just log)
                print(f"   ✅ +1 Point added to {referrer.full_name}")
                
                recovered_count += 1
                
            except Exception as e:
                print(f"❌ Error processing log {log.id}: {e}")
        
        session.commit()
        print(f"\n🎉 Recovery Complete. Total recovered: {recovered_count}")

if __name__ == "__main__":
    recover_missing_referrals()
