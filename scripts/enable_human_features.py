from core.db import db

def enable_flags():
    admin_id = 6770204468
    print("Enabling new Human-Centered flags for Admin...")
    
    # 1. Coach Zone
    db.set_feature_flag("coach_zone_v1", enabled=True, rollout_percent=0, allowlist=[admin_id])
    print("✅ coach_zone_v1")
    
    # 2. Menu Swap
    db.set_feature_flag("menu_swap_v1", enabled=True, rollout_percent=0, allowlist=[admin_id])
    print("✅ menu_swap_v1")
    
    # 3. Soft Workout
    db.set_feature_flag("soft_workout_mode", enabled=True, rollout_percent=0, allowlist=[admin_id])
    print("✅ soft_workout_mode")
    
    # 4. Weekly Feedback
    db.set_feature_flag("weekly_progress_feedback", enabled=True, rollout_percent=0, allowlist=[admin_id])
    print("✅ weekly_progress_feedback")

if __name__ == "__main__":
    enable_flags()
