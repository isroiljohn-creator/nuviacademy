"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel
from typing import Optional, List


# ── User ─────────────────────────────────
class UserProfile(BaseModel):
    telegram_id: int
    name: Optional[str] = None
    age: Optional[int] = None
    goal_tag: Optional[str] = None
    level_tag: Optional[str] = None
    lead_score: int = 0
    lead_segment: str = "content_only"
    user_status: str = "started"
    subscription_status: str = "inactive"
    registered_at: Optional[str] = None


# ── Referral ─────────────────────────────
class ReferralStats(BaseModel):
    referral_link: str
    total_invited: int = 0
    valid_referrals: int = 0
    paid_referrals: int = 0
    balance: int = 0
    club_price: int = 97_000
    amount_for_free: int = 0  # how much more needed for free sub


# ── Payment ──────────────────────────────
class PaymentInitRequest(BaseModel):
    provider: str = "click"  # click | payme


class PaymentInitResponse(BaseModel):
    payment_id: int
    base_price: int
    referral_discount: int
    final_price: int
    payment_url: str


# ── Course ───────────────────────────────
class CourseModuleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    order: int
    is_locked: bool = False
    completion_pct: float = 0.0
    is_completed: bool = False


class CourseProgressRequest(BaseModel):
    module_id: int
    watch_time: int = 0      # seconds
    completion_pct: float = 0.0


# ── Guides ───────────────────────────────
class GuideCreate(BaseModel):
    title: str
    content: Optional[str] = None
    file_id: Optional[str] = None
    file_type: Optional[str] = None
    media_url: Optional[str] = None
    is_active: bool = True
    order: int = 0


class GuideUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    file_id: Optional[str] = None
    file_type: Optional[str] = None
    media_url: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class GuideResponse(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    file_id: Optional[str] = None
    file_type: Optional[str] = None
    media_url: Optional[str] = None
    is_active: bool
    order: int
    created_at: str


# ── Lead Magnet ─────────────────────────────
class LeadMagnetCreate(BaseModel):
    campaign: str
    content_type: str
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class LeadMagnetUpdate(BaseModel):
    campaign: Optional[str] = None
    content_type: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class LeadMagnetResponse(BaseModel):
    id: int
    campaign: str
    content_type: str
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: str


# ── Webhook ──────────────────────────────
class ClickWebhookData(BaseModel):
    click_trans_id: int
    service_id: int
    click_paydoc_id: int
    merchant_trans_id: str
    amount: float
    action: int
    error: int
    error_note: str
    sign_time: str
    sign_string: str


class PaymeWebhookData(BaseModel):
    method: str
    params: dict


# ── Admin Settings ───────────────────────────
class AdminSettingResponse(BaseModel):
    key: str
    value: str
    updated_at: str


class AdminSettingUpdate(BaseModel):
    value: str
