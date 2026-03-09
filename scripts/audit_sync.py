from core.db import db, get_sync_db
from backend.models import User, Plan, UserMenuLink, MenuTemplate, FriendRequest
from sqlalchemy import text, func
import datetime

def run_audit():
    print("🔎 STARTING FULL DATABASE AUDIT...")
    print("-" * 50)
    
    with get_sync_db() as session:
        # 1. Total Users
        total_users = session.query(User).count()
        premium_users = session.query(User).filter(User.is_premium == True).count()
        print(f"👥 Total Users: {total_users}")
        print(f"💎 Premium Users: {premium_users}")
        
        # 2. Menu Sync Audit
        active_links = session.query(UserMenuLink).filter(UserMenuLink.is_active == True).count()
        print(f"🔗 Active Menu Links: {active_links}")
        
        # Premium users WITHOUT active menu (Missed generation?)
        # Only meaningful if they actually tried to generate.
        # But we can check if they have Legacy Plan but NO Menu Link (Migration candidate)
        legacy_only = session.execute(text("""
            SELECT count(*) FROM plans p 
            JOIN users u ON u.id = p.user_id 
            WHERE p.type='meal' 
            AND u.is_premium = true
            AND u.id NOT IN (SELECT user_id FROM user_menu_links WHERE is_active=true)
        """)).scalar()
        print(f"⚠️ Premium Users with Legacy Plan ONLY (No Sync Link): {legacy_only}")
        
        # 3. Legacy Plan Ghosting (The bug I fixed)
        # Plans created in last 24h vs Active Links
        recent_plans = session.execute(text("""
            SELECT count(*) FROM plans 
            WHERE type='meal' 
            AND created_at > NOW() - INTERVAL '24 HOURS'
        """)).scalar()
        
        recent_links = session.execute(text("""
            SELECT count(*) FROM user_menu_links 
            WHERE start_date > NOW() - INTERVAL '24 HOURS'
        """)).scalar()
        
        print(f"📅 Last 24h: New Legacy Plans: {recent_plans}")
        print(f"📅 Last 24h: New Menu Links: {recent_links}")
        if recent_plans > 0 and recent_plans > recent_links:
             print("   Note: If New Legacy Plans > 0, ensure they are workouts or pre-fix meal plans.")
        
        # DEBUG USER 1
        u1_plans = session.execute(text("SELECT count(*) FROM plans WHERE user_id=1 AND type='meal'")).scalar()
        u1_links = session.execute(text("SELECT count(*) FROM user_menu_links WHERE user_id=1")).scalar()
        u1_active = session.execute(text("SELECT count(*) FROM user_menu_links WHERE user_id=1 AND is_active=true")).scalar()
        
        print(f"👤 User 1 Debug:")
        print(f"   - Total Legacy Plans (Meal): {u1_plans}")
        print(f"   - Total Menu Links: {u1_links}")
        print(f"   - Active Menu Links: {u1_active}")
        
        if u1_plans > 0 and u1_active == 0:
            print("   ⚠️ User 1 has legacy plans but NO active link. This explains missing menu!")
            
        # 4. Referral Integrity
        orphan_referrals = session.execute(text("""
            SELECT count(*) FROM users 
            WHERE referrer_id IS NOT NULL 
            AND referrer_id NOT IN (SELECT id FROM users)
        """)).scalar()
        if orphan_referrals > 0:
            print(f"❌ Orphan Referrals (Referrer deleted): {orphan_referrals}")
        else:
            print("✅ Referral Integrity: OK")
            
        # 5. Usage Counter Check
        # Ensure counters exist for active users (created on demand so ok if missing)
        counters = session.execute(text("SELECT count(*) FROM usage_counters")).scalar()
        print(f"📊 Usage Counters: {counters}")
        
        # 6. Friend Request Stale
        # Pending requests older than 7 days
        stale_reqs = session.execute(text("""
            SELECT count(*) FROM friend_requests 
            WHERE status='pending' 
            AND created_at < NOW() - INTERVAL '7 DAYS'
        """)).scalar()
        print(f"⏳ Stale Friend Requests (>7 days): {stale_reqs}")

        # 7. Duplicate Telegram IDs (Should be 0 due to unique constraint, but good to check logic)
        dupes = session.execute(text("""
            SELECT telegram_id, count(*) as c 
            FROM users 
            GROUP BY telegram_id 
            HAVING count(*) > 1
        """)).fetchall()
        if dupes:
            print(f"‼️ DUPLICATE TELEGRAM IDS FOUND: {len(dupes)}")
        else:
            print("✅ User Uniqueness: OK")

        # 8. Check Feature Flags
        flags = session.execute(text("SELECT key, enabled FROM feature_flags")).fetchall()
        print("🚩 Feature Flags:")
        for key, enabled in flags:
            print(f"   - {key}: {'ON' if enabled else 'OFF'}")

    print("-" * 50)
    print("✅ AUDIT COMPLETE")

if __name__ == "__main__":
    run_audit()
