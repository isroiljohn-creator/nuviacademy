
from core.db import db
import json

def check_flags():
    flags = [
        "feedback_v1",
        "smart_paywall",
        "stateful_ai_context",
        "founder_tone",
        "phase7_explain_v1"
    ]
    
    print("--- Feature Flag Audit ---")
    for key in flags:
        flag = db.get_feature_flag(key)
        if flag:
            print(f"Flag: {key}")
            print(f"  Enabled: {flag['enabled']}")
            print(f"  Rollout: {flag['rollout_percent']}%")
            print(f"  Allowlist: {flag.get('allowlist')}")
        else:
            print(f"Flag: {key} -> NOT FOUND in DB (default=False)")

if __name__ == "__main__":
    check_flags()
