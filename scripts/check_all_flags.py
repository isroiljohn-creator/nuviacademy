
from core.db import db
import json

def check_all_flags():
    flags = db.get_all_feature_flags()
    
    print(f"{'Flag Key':<30} | {'Enabled':<8} | {'Rollout':<8} | {'Allowlist':<20}")
    print("-" * 80)
    for f in flags:
        key = f['key']
        enabled = str(f['enabled'])
        rollout = f"{f['rollout_percent']}%"
        allowlist = f.get('allowlist', '[]')
        print(f"{key:<30} | {enabled:<8} | {rollout:<8} | {allowlist:<20}")

if __name__ == "__main__":
    check_all_flags()
