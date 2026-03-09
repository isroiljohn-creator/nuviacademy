import sys
import os

# Identify root directory
sys.path.append(os.getcwd())

from bot.analytics_pro import get_investor_snapshot, get_feedback_adaptation_report, get_ai_cost_report
from core.db import db
from backend.database import get_sync_db

# Function to run tests
def verify_analytics():
    print("🚀 Verifying Analytics Pro Dashboard...\n")

    try:
        print("📌 Generating Investor Snapshot (7d)...")
        snap = get_investor_snapshot(7)
        print(f"✅ Success! Report First 100 chars: {snap[:100]}...\n")
        # printFull report if needed
        # print(snap)

    except Exception as e:
        print(f"❌ Snapshot Failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        print("🧠 Generating Feedback & Adaptation Report...")
        adapt = get_feedback_adaptation_report()
        print(f"✅ Success! Report First 100 chars: {adapt[:100]}...\n")

    except Exception as e:
        print(f"❌ Adaptation Failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        print("💸 Generating AI Cost Report...")
        cost = get_ai_cost_report()
        print(f"✅ Success! Report First 100 chars: {cost[:100]}...\n")

    except Exception as e:
        print(f"❌ Cost Report Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_analytics()
