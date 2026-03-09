import time
import traceback
from core.db import db
from functools import wraps

def log_event(event_type, user_id=None, meta=None, success=True, latency=None):
    """
    Log an event to the DB asynchronously.
    """
    try:
        db.log_admin_event(
            event_type=event_type,
            user_id=user_id,
            success=success,
            latency_ms=latency,
            meta=meta
        )
    except Exception as e:
        print(f"LOG_EVENT_ERROR: {e}")

def track_latency(event_type):
    """Decorator to measure latency and log event automagically"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            user_id = None
            success = True
            error_meta = None
            
            # Try to extract user_id from first arg (message/call)
            if args:
                obj = args[0]
                if hasattr(obj, 'from_user') and obj.from_user:
                    user_id = obj.from_user.id
                elif hasattr(obj, 'chat') and obj.chat:
                    user_id = obj.chat.id
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_meta = {
                    "error": str(e),
                    "stack_trace": traceback.format_exc()
                }
                raise e
            finally:
                duration = (time.time() - start) * 1000
                log_event(
                    event_type=event_type,
                    user_id=user_id,
                    success=success,
                    latency=duration,
                    meta=error_meta
                )
        return wrapper
    return decorator
