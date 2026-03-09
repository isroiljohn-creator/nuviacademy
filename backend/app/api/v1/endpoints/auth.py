from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models import User
from backend.auth import create_access_token
from pydantic import BaseModel
from urllib.parse import parse_qsl
import hmac
import hashlib
import json
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()

# Get limiter from app state or create fallback
# Note: In router file, we usually need access to the app instance or use dependency injection.
# For simplicity in this architecture, we'll use request.app.state.limiter mechanism via decorator

class TelegramAuthRequest(BaseModel):
    initData: str

@router.post("/telegram")
@Limiter(key_func=get_remote_address).limit("5/minute")
async def telegram_auth(req: TelegramAuthRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate via Telegram WebApp initData (Rate Limit: 5/min)"""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not set")

    print(f"DEBUG: Auth request received. initData length: {len(req.initData)}")
    try:
        parsed_data = dict(parse_qsl(req.initData))
    except ValueError:
        print("DEBUG: Invalid initData format")
        raise HTTPException(status_code=401, detail="Invalid initData format")
    
    if "hash" not in parsed_data:
        print("DEBUG: Missing hash in initData")
        raise HTTPException(status_code=401, detail="Missing hash")

    hash_ = parsed_data.pop("hash")
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )
    
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_:
        print(f"DEBUG: Hash mismatch! Calc: {calculated_hash}, Recv: {hash_}")
        print(f"DEBUG: Data string: {data_check_string}")
        raise HTTPException(status_code=403, detail="Invalid hash")
    
    print("DEBUG: Hash valid. Proceeding to user lookup.")
    
    user_data = json.loads(parsed_data.get("user", "{}"))
    telegram_id = int(user_data.get("id"))
    
    # Get or create user
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            full_name=user_data.get("first_name", "") + " " + user_data.get("last_name", ""),
            referral_code=f"r{telegram_id}"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    token = create_access_token({"user_id": user.id, "telegram_id": telegram_id})
    is_admin = telegram_id == int(os.getenv("ADMIN_ID", 0))
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "is_premium": user.is_premium,
            "is_onboarded": user.is_onboarded,
            "is_admin": is_admin,
            "bot_username": os.getenv("BOT_USERNAME", "YashaBot")
        }
    }
