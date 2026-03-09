
from core.db import db

def enable_feedback():
    print("Enabling feedback_v1 for 100% of users...")
    db.set_feature_flag("feedback_v1", True, rollout_percent=100, allowlist=[])
    
    flag = db.get_feature_flag("feedback_v1")
    print(f"Update successful: {flag}")

if __name__ == "__main__":
    enable_feedback()
