"""SQLAlchemy async models — full PostgreSQL schema."""
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Float,
    ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String(20), nullable=True)
    phone_hash = Column(String(64), nullable=True, unique=True)

    # Source tracking
    source = Column(String(50), nullable=True)           # instagram, telegram, etc.
    campaign = Column(String(100), nullable=True)         # lead_dars, lead_checklist, lead_vsl
    referer_id = Column(BigInteger, nullable=True)        # telegram_id of referer

    # Status
    user_status = Column(
        String(20), default="started", nullable=False
    )  # started | registered

    # Segmentation
    goal_tag = Column(String(30), nullable=True)    # make_money | get_clients | automate_business
    level_tag = Column(String(20), nullable=True)   # beginner | freelancer | business

    # Lead scoring
    lead_score = Column(Integer, default=0, nullable=False)
    lead_segment = Column(String(20), default="content_only")  # hot | nurture | content_only

    # Flags
    lead_magnet_opened = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_at = Column(DateTime, nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    referral_balance = relationship("ReferralBalance", back_populates="user", uselist=False)
    events = relationship("Event", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")

    __table_args__ = (
        Index("ix_users_lead_segment", "lead_segment"),
        Index("ix_users_campaign", "campaign"),
        Index("ix_users_user_status", "user_status"),
    )


# ──────────────────────────────────────────────
# Subscriptions
# ──────────────────────────────────────────────
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    status = Column(String(20), default="inactive")  # active | inactive | cancelled | expired
    plan = Column(String(30), default="monthly")
    price = Column(Integer, nullable=False)
    card_token = Column(String(255), nullable=True)

    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscription")


# ──────────────────────────────────────────────
# Referrals
# ──────────────────────────────────────────────
class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referer_id = Column(BigInteger, nullable=False, index=True)      # telegram_id of who referred
    referred_id = Column(BigInteger, nullable=False, unique=True)    # telegram_id of referred user
    status = Column(String(20), default="pending")  # pending | valid | paid | flagged
    reward_amount = Column(Integer, default=0)
    phone_hash = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)


class ReferralBalance(Base):
    __tablename__ = "referral_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0)        # current available balance (UZS)
    total_earned = Column(Integer, default=0)   # lifetime earned
    total_used = Column(Integer, default=0)     # used towards payments

    user = relationship("User", back_populates="referral_balance")


# ──────────────────────────────────────────────
# Events (analytics)
# ──────────────────────────────────────────────
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # lead, registration_complete, vsl_view, etc.
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="events")

    __table_args__ = (
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_user_created", "user_id", "created_at"),
    )


# ──────────────────────────────────────────────
# Content — Lead magnets
# ──────────────────────────────────────────────
class LeadMagnet(Base):
    __tablename__ = "lead_magnets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign = Column(String(100), unique=True, nullable=False)  # lead_dars, lead_checklist, lead_vsl
    content_type = Column(String(30), nullable=False)            # video, pdf, vsl
    file_id = Column(String(255), nullable=True)                 # Telegram file_id
    file_url = Column(Text, nullable=True)                       # external URL
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ──────────────────────────────────────────────
# Content — VSL per segment
# ──────────────────────────────────────────────
class VSLContent(Base):
    __tablename__ = "vsl_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level_tag = Column(String(20), nullable=False)
    goal_tag = Column(String(30), nullable=True)
    video_file_id = Column(String(255), nullable=True)
    video_url = Column(Text, nullable=True)
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_vsl_segment", "level_tag", "goal_tag"),
    )


# ──────────────────────────────────────────────
# Course modules (Mini App)
# ──────────────────────────────────────────────
class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(Text, nullable=True)
    video_file_id = Column(String(255), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    unlock_condition = Column(String(100), nullable=True)  # e.g. "module_1_complete", "vsl_watched"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("course_modules.id"), nullable=False)
    watch_time = Column(Integer, default=0)          # seconds
    completion_pct = Column(Float, default=0.0)      # 0.0 – 100.0
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="progress")
    module = relationship("CourseModule")

    __table_args__ = (
        UniqueConstraint("user_id", "module_id", name="uq_user_module"),
    )


# ──────────────────────────────────────────────
# Payments
# ──────────────────────────────────────────────
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)              # UZS
    referral_discount = Column(Integer, default=0)        # amount deducted from referral balance
    provider = Column(String(30), nullable=False)         # click | payme
    status = Column(String(20), default="pending")        # pending | success | failed | refunded
    transaction_id = Column(String(255), nullable=True)
    webhook_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_status", "status"),
    )


# ──────────────────────────────────────────────
# Broadcast
# ──────────────────────────────────────────────
class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filters = Column(JSON, nullable=True)        # {"source":"instagram","lead_score_min":30}
    content_type = Column(String(20), nullable=False)  # text | photo | video
    content = Column(Text, nullable=False)
    file_id = Column(String(255), nullable=True)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")  # draft | sending | completed | cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime, nullable=True)


# ──────────────────────────────────────────────
# Funnel triggers (no-code rules)
# ──────────────────────────────────────────────
class FunnelTrigger(Base):
    __tablename__ = "funnel_triggers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    event = Column(String(50), nullable=False)           # event_type that triggers this
    condition = Column(JSON, nullable=True)               # additional conditions
    action = Column(String(30), nullable=False)           # send_message | send_video | delay_send
    message_template = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)
    delay_seconds = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ──────────────────────────────────────────────
# Admin settings
# ──────────────────────────────────────────────
class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ──────────────────────────────────────────────
# Guides (Qo'llanmalar)
# ──────────────────────────────────────────────
class Guide(Base):
    __tablename__ = "guides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)                 # Long text or description
    file_id = Column(String(255), nullable=True)          # Telegram file ID (PDF, Video, etc.)
    file_type = Column(String(50), nullable=True)         # document, video, photo, text
    media_url = Column(Text, nullable=True)               # External URL (e.g., YouTube)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

