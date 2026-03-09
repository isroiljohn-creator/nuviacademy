
from core.db import db

def enable_all_flags():
    flags = [
        "stateful_ai_context",
        "progress_insights",
        "retention_engine",
        "smart_paywall",
        "founder_tone",
        "db_menu_assembly",
        "db_workout_assembly",
        "coach_zone_v1",
        "menu_swap_v1",
        "soft_workout_mode",
        "weekly_progress_feedback",
        "adaptation_v1",
        "optimization_v1",
        "feedback_v1",
        "phase7_explain_v1"
    ]
    
    print("Enabling all pending feature flags to 100% rollout...")
    for key in flags:
        print(f"Setting {key} -> True (100%)")
        db.set_feature_flag(key, True, rollout_percent=100, allowlist=[])
    
    print("\nFinal Status Audit:")
    all_flags = db.get_all_feature_flags()
    print(f"{'Flag Key':<30} | {'Enabled':<8} | {'Rollout':<8}")
    print("-" * 50)
    for f in all_flags:
        print(f"{f['key']:<30} | {str(f['enabled']):<8} | {f['rollout_percent']}%")

if __name__ == "__main__":
    enable_all_flags()
