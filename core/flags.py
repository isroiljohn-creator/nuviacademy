import json
import hashlib
from core.db import db

# Global Kill Switches (Feature Flag Keys)
KILL_SWITCH_AI = "disable_ai_generation"
KILL_SWITCH_OPTIMIZATION = "disable_optimization"
KILL_SWITCH_READ_ONLY = "read_only_mode"

def is_system_readonly() -> bool:
    """Check if system is in read-only mode (maintenance)."""
    return is_flag_enabled(KILL_SWITCH_READ_ONLY, default=False)


def is_flag_enabled(key: str, user_id: int = None, default: bool = False) -> bool:
    """
    Check if a feature flag is enabled for a specific user using deterministic rollout.
    
    Logic:
    1. Check DB for flag. If missing -> return default.
    2. If allowlist contains user -> True.
    3. If denylist contains user -> False.
    4. If enabled is False -> False.
    5. If enabled is True:
       - If rollout_percent == 100 -> True.
       - Else: Hash(user_id + key) % 100 < rollout.
    """
    flag = db.get_feature_flag(key)
    
    # 1. Missing flag
    if not flag:
        return default
        
    # User-specific logic (only if user_id is provided)
    if user_id:
        try:
            allowlist = json.loads(flag.get('allowlist', '[]') or '[]')
            if user_id in allowlist: return True
            
            denylist = json.loads(flag.get('denylist', '[]') or '[]')
            if user_id in denylist: return False
        except:
            pass # Json error, ignore lists

    # 4. Global Switch
    if not flag['enabled']:
        return False
        
    # 5. Rollout Logic
    rollout = flag.get('rollout_percent', 0)
    if rollout >= 100:
        return True
    
    if rollout <= 0:
        return False
        
    if user_id:
        # Deterministic Hash
        # hash_val = int(md5(f"{user_id}:{key}".encode()).hexdigest(), 16) % 100
        hash_input = f"{user_id}:{key}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100
        return hash_val < rollout
        
    # If no user_id but flag is partial rollout, what to do?
    # Usually default to False (safe) or True (if we want global test).
    # "New Workout v2" requires user context.
    # Let's return False if user_id missing but rollout < 100.
    return False
