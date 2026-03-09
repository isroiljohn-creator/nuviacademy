
import os
import sys
import time
import threading
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

# MOCK ENVIRONMENT for Verification
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"

def test_postgres_enforcement():
    print("--- Testing Postgres Enforcement ---")
    try:
        from core import config
        # We cannot verify crash unless we subprocess, but we can verify code snippets exist
        with open("core/config.py", "r") as f:
            content = f.read()
            if "sqlite" in content and "sys.exit(1)" in content:
                 print("✅ SQLite rejection logic found in config.py")
            else:
                 print("⚠️ SQLite rejection logic MIGHT be missing")
                 
        with open("backend/database.py", "r") as f:
             content = f.read()
             if "PRAGMA journal_mode=WAL" not in content:
                  print("✅ WAL Mode (SQLite specific) removed from database.py")
             else:
                  print("❌ WAL Mode still present!")
    except Exception as e:
        print(f"❌ Config Error: {e}")

def test_alembic_setup():
     print("\n--- Testing Alembic Setup ---")
     if os.path.exists("alembic") and os.path.exists("alembic.ini"):
          print("✅ Alembic folder exists")
     else:
          print("❌ Alembic missing")
          
     versions = os.listdir("alembic/versions")
     if len(versions) >= 2: # __pycache__ + 2 migrations
          print(f"✅ Migrations found: {len(versions)} files")
     else:
          print("⚠️ Few migrations found")

def test_broadcast_threading():
    print("\n--- Testing Broadcast Threading ---")
    try:
        from bot import admin
        
        # Mock objects
        mock_bot = MagicMock()
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "Test Broadcast"
        mock_message.content_type = 'text'
        
        # Patch _broadcast_worker to avoid actual DB calls/spam
        original_worker = admin._broadcast_worker
        
        worker_called = threading.Event()
        
        def mock_worker(message, bot, segment):
            print("🧵 Worker thread started!")
            time.sleep(0.1)
            print("🧵 Worker thread finished!")
            worker_called.set()
            
        admin._broadcast_worker = mock_worker
        
        print("🚀 Invoking process_broadcast...")
        start_time = time.time()
        admin.process_broadcast(mock_message, mock_bot, "all")
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱ Main thread return time: {duration:.4f}s")
        
        if duration < 0.1:
            print("✅ Main thread non-blocking")
        else:
            print("❌ Main thread BLOCKED")
            
        # Wait for worker
        worker_called.wait(timeout=1)
        if worker_called.is_set():
            print("✅ Worker thread executed")
        else:
            print("❌ Worker thread did not execute")
            
        # Restore
        admin._broadcast_worker = original_worker

    except Exception as e:
        print(f"❌ Broadcast Error: {e}")

def test_input_validation():
    print("\n--- Testing Input Validation ---")
    try:
        # MOCK core.db to avoid DB connection
        mock_db_module = MagicMock()
        mock_db_instance = MagicMock()
        mock_db_module.db = mock_db_instance
        sys.modules['core.db'] = mock_db_module
        
        # Now import bot modules which will use the mocked db
        from bot import onboarding, trackers
        
        # Mock Bot
        mock_bot = MagicMock()
        mock_bot.send_message = MagicMock()
        
        # Mock Manager
        # onboarding.manager is imported from onboarding
        # If we mock core.db, what about core.utils? 
        # onboarding imports utils. safe_handler etc. Utils is fine.
        
        # We need to ensure onboarding.manager.get_state works
        # onboarding.py: manager = OnboardingManager()
        # OnboardingManager uses db.get_onboarding_state
        # Since we mocked db, manager calls mock_db_instance.get_onboarding_state
        # We can just mock manager.get_state directly.
        
        onboarding.manager.get_state = MagicMock(return_value=onboarding.STATE_AGE)
        
        # 1. Test Sticker (Non-text) for Age
        print("Testing Sticker Input for Age...")
        msg_sticker = MagicMock()
        msg_sticker.from_user.id = 111
        msg_sticker.content_type = 'sticker'
        msg_sticker.text = None
        
        onboarding.process_age(msg_sticker, mock_bot)
        
        # Verify strict error message
        # process_age calls send_message with "...matn..." or similar
        args_list = mock_bot.send_message.call_args_list
        if args_list:
             last_args = args_list[-1][0]
             print(f"Response: {last_args[1]}")
             if "matn" in last_args[1].lower() or "raqam" in last_args[1].lower():
                 print("✅ Correctly rejected sticker")
             else:
                 print(f"⚠️ Unexpected response: {last_args[1]}")
        else:
             print("❌ No response sent!")
             
        # 2. Test Sticker for Trackers (Steps)
        print("Testing Sticker Input for Steps...")
        trackers.process_steps_input(msg_sticker, mock_bot)
        args_list = mock_bot.send_message.call_args_list
        if args_list:
             last_args = args_list[-1][0]
             print(f"Response: {last_args[1]}")
             if "faqat raqam" in last_args[1].lower():
                 print("✅ Correctly rejected sticker in Trackers")
             else:
                 print(f"⚠️ Unexpected response: {last_args[1]}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Input Validation Error: {e}")

if __name__ == "__main__":
    # GLOBAL MOCK of core.db to allow imports without DB connection
    mock_db_module = MagicMock()
    mock_db_instance = MagicMock()
    mock_db_module.db = mock_db_instance
    sys.modules['core.db'] = mock_db_module

    test_postgres_enforcement()
    test_alembic_setup()
    test_broadcast_threading()
    test_input_validation()
