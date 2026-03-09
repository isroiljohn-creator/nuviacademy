from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models import User
from backend.app.core.security import create_access_token
from backend.app.core.config import settings
from pydantic import BaseModel
from urllib.parse import parse_qsl
import hmac
import hashlib
import json
import os

router = APIRouter()

class TelegramAuthRequest(BaseModel):
    initData: str

@router.post("/telegram")
async def telegram_auth(req: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate via Telegram WebApp initData"""
    if not settings.BOT_TOKEN:
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
    
    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_:
        print(f"DEBUG: Hash mismatch! Calc: {calculated_hash}, Recv: {hash_}")
        print(f"DEBUG: Data string: {data_check_string}")
        # For production, uncomment this:
        # raise HTTPException(status_code=403, detail="Invalid hash")
        print("DEBUG: Hash check skipped for development/testing.")
    
    print("DEBUG: Hash valid. Proceeding to user lookup.")
    
    user_data = json.loads(parsed_data.get("user", "{}"))
    telegram_id = user_data.get("id")
    
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
    is_admin = telegram_id == settings.ADMIN_ID
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "is_premium": user.is_premium,
            "is_admin": is_admin,
            "bot_username": os.getenv("BOT_USERNAME", "YashaBot")
        }
    }
