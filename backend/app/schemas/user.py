from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = Field(None, ge=10, le=100)
    gender: Optional[str] = None
    height: Optional[float] = Field(None, ge=100, le=250)
    weight: Optional[float] = Field(None, ge=30, le=300)
    target_weight: Optional[float] = Field(None, ge=30, le=300)
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    allergies: Optional[str] = None
    language: Optional[str] = None
    notification_settings: Optional[dict] = None

class TelegramAuthRequest(BaseModel):
    initData: str

class DailyTaskUpdate(BaseModel):
    task_type: str  # water, workout, steps
    value: bool | int
