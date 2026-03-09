import requests
import hmac
import hashlib
import json
import time
import os
import sys

# Add root path
sys.path.append(os.getcwd())
from core.config import BOT_TOKEN, ADMIN_IDS

def generate_init_data(user_id, admin=True):
    # If admin=False, use a random ID not in ADMIN_IDS
    if not admin:
        user_id = 999999999
        while user_id in ADMIN_IDS:
            user_id += 1
            
    user_data = json.dumps({"id": user_id, "first_name": "Test", "username": "tester"})
    auth_date = int(time.time())
    
    data_dict = {
        "auth_date": str(auth_date),
        "user": user_data,
        "query_id": "test_query_id"
    }
    
    # Sort and create check string
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    
    # Sign
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    # Return as URL encoded string (mocking what frontend sends)
    # Actually client sends raw string from WebApp.initData, which is "key=val&key=val&hash=..."
    # But keys must be sorted alphabetically in the string for hash mismatch?
    # Telegram web sends it in some order. Be careful.
    # The verification code sorts it. So we just need to provide params.
    
    init_data = f"auth_date={auth_date}&query_id=test_query_id&user={user_data}&hash={hash_val}"
    return init_data

def verify_integration():
    print("🚀 Verifying Admin App Integration...")
    
    # NOTE: This script assumes the Backend is RUNNING on localhost:8000
    # Since in this environment we cannot easily start background server,
    # we will mock the request or just print the curl command.
    # User said "Provide exact verification steps".
    # I will output the Curl commands.
    
    admin_id = ADMIN_IDS[0] if ADMIN_IDS else 12345
    admin_init_data = generate_init_data(admin_id, admin=True)
    user_init_data = generate_init_data(admin_id, admin=False)
    
    print("\n🔹 1. Admin Auth (Should Succeed)")
    print(f"CURL Command:")
    print(f"curl -X POST http://localhost:8000/api/v1/auth/telegram \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{{\"initData\": \"{admin_init_data}\"}}'")
    
    print("\n🔹 2. Non-Admin Auth (Should Fail 403)")
    print(f"CURL Command:")
    print(f"curl -X POST http://localhost:8000/api/v1/auth/telegram \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{{\"initData\": \"{user_init_data}\"}}'")
    
    print("\n🔹 3. Get Stats (Requires Token)")
    print(f"curl http://localhost:8000/api/v1/admin/stats -H 'Authorization: Bearer <TOKEN>'")

if __name__ == "__main__":
    verify_integration()
