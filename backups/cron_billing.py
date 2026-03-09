import schedule
import time
import os
from datetime import datetime, timedelta
from core.db import db
from dotenv import load_dotenv

load_dotenv()

# Mock function to simulate charging a card
def charge_user(user_id, amount):
    # In a real app, this would use a saved provider_token or card token
    # For now, we simulate success
    print(f"Charging user {user_id} amount {amount}...")
    return True

def check_subscriptions():
    print(f"Running subscription check at {datetime.now()}")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Find users whose premium has expired AND have auto_renew=1
    now = datetime.now().isoformat()
    cursor.execute("SELECT telegram_id, premium_until FROM users WHERE auto_renew = 1 AND premium_until < ?", (now,))
    users = cursor.fetchall()
    
    for user_id, premium_until in users:
        print(f"Processing renewal for {user_id} (Expired: {premium_until})")
        
        # Attempt charge (Mock)
        # 49,000 UZS for 30 days
        if charge_user(user_id, 49000):
            # Extend for 30 days
            db.set_premium(user_id, 30)
            print(f"Successfully renewed for {user_id}")
            # Ideally send a notification via bot (requires bot instance)
        else:
            # Failed charge
            print(f"Failed to renew for {user_id}")
            # Disable auto-renew
            cursor.execute("UPDATE users SET auto_renew = 0 WHERE telegram_id = ?", (user_id,))
            conn.commit()
            
    conn.close()

# Schedule the job every day at 09:00
schedule.every().day.at("09:00").do(check_subscriptions)

# Also run once on startup for testing
check_subscriptions()

if __name__ == "__main__":
    print("Starting Billing Cron Service...")
    while True:
        schedule.run_pending()
        time.sleep(60)
