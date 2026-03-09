from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models import User
from backend.app.core.security import verify_token
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.id == payload["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    allergies: Optional[str] = None

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "age": current_user.age,
        "gender": current_user.gender,
        "height": current_user.height,
        "weight": current_user.weight,
        "target_weight": current_user.target_weight,
        "goal": current_user.goal,
        "activity_level": current_user.activity_level,
        "allergies": current_user.allergies,
        "is_premium": current_user.is_premium,
        "premium_until": current_user.premium_until,
        "points": current_user.points,
        "referral_code": current_user.referral_code,
        "bot_username": os.getenv("BOT_USERNAME", "YashaBot")
    }

@router.put("/profile")
async def update_profile(
    update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    for key, value in update.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    await db.commit()
    return {"status": "updated"}
