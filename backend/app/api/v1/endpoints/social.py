from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, func
from backend.database import get_db
from backend.models import User, FriendRequest, Friendship, Challenge, ChallengeParticipant
from backend.app.api.v1.endpoints.users import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class ChallengeCreate(BaseModel):
    title: str
    type: str
    target_value: int
    days: int

@router.get("/search")
async def search_users(q: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Search users by username (with or without @)"""
    if len(q) < 3:
        return []
    
    search_q = q.lstrip("@").lower()
    result = await db.execute(
        select(User).where(User.username.ilike(f"%{search_q}%")).limit(10)
    )
    users = result.scalars().all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name} for u in users if u.id != current_user.id]

@router.post("/friends/request")
async def send_friend_request(to_user_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="O'zingizga so'rov yubora olmaysiz")
    
    # Check if target exists
    target = await db.get(User, to_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    # Check if already friends
    res = await db.execute(select(Friendship).where(
        or_(
            and_(Friendship.user_id == current_user.id, Friendship.friend_id == to_user_id),
            and_(Friendship.user_id == to_user_id, Friendship.friend_id == current_user.id)
        )
    ))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Allaqachon do'stsiz")

    # Check for existing pending request
    res = await db.execute(select(FriendRequest).where(
        and_(FriendRequest.from_user_id == current_user.id, FriendRequest.to_user_id == to_user_id, FriendRequest.status == "pending")
    ))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="So'rov allaqachon yuborilgan")

    new_req = FriendRequest(from_user_id=current_user.id, to_user_id=to_user_id)
    db.add(new_req)
    await db.commit()
    return {"status": "success"}

@router.get("/friends/requests")
async def get_friend_requests(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get pending friend requests received by the current user"""
    res = await db.execute(
        select(FriendRequest)
        .where(and_(FriendRequest.to_user_id == current_user.id, FriendRequest.status == "pending"))
        .order_by(desc(FriendRequest.created_at))
    )
    requests = res.scalars().all()
    
    output = []
    for req in requests:
        # Get sender info
        sender = await db.get(User, req.from_user_id)
        if sender:
            output.append({
                "id": str(req.id),
                "fromUser": {
                    "id": str(sender.id),
                    "name": sender.full_name or sender.username or "Foydalanuvchi",
                    "level": (sender.points // 100) + 1
                },
                "createdAt": req.created_at.isoformat()
            })
    return output

@router.post("/friends/requests/{request_id}/accept")
async def accept_friend_request(request_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Get request
    req = await db.get(FriendRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    
    if req.to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="So'rov allaqachon yakunlangan")
        
    # Update status
    req.status = "accepted"
    
    # Create Friendship (Mutual)
    f1 = Friendship(user_id=req.from_user_id, friend_id=req.to_user_id)
    f2 = Friendship(user_id=req.to_user_id, friend_id=req.from_user_id)
    
    db.add(f1)
    db.add(f2)
    
    await db.commit()
    return {"status": "success"}

@router.post("/friends/requests/{request_id}/decline")
async def decline_friend_request(request_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    req = await db.get(FriendRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    
    if req.to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        
    req.status = "rejected"
    await db.commit()
    return {"status": "success"}

@router.get("/friends")
async def get_friends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Query friendships where the current user is either user_id or friend_id
    res = await db.execute(select(Friendship).where(Friendship.user_id == current_user.id))
    fships = res.scalars().all()
    
    friends_list = []
    for fs in fships:
        # Load friend data
        f_res = await db.execute(select(User).where(User.id == fs.friend_id))
        f = f_res.scalar_one_or_none()
        if f:
            friends_list.append({
                "id": str(f.id),
                "name": f.full_name or f.username or "Foydalanuvchi",
                "level": (f.points // 100) + 1,
                "xp": f.points,
                "status": "online" # Mock for now
            })
    return friends_list

@router.post("/challenges")
async def create_challenge(challenge: ChallengeCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_c = Challenge(
        creator_id=current_user.id,
        title=challenge.title,
        type=challenge.type,
        target_value=challenge.target_value,
        days=challenge.days
    )
    db.add(new_c)
    await db.flush() # Get id
    
    # Creator joins automatically
    participant = ChallengeParticipant(challenge_id=new_c.id, user_id=current_user.id)
    db.add(participant)
    
    await db.commit()
    return {"status": "success", "id": new_c.id}

@router.get("/challenges")
async def get_challenges(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Challenge).where(Challenge.status == "active").order_by(desc(Challenge.id)))
    challenges = res.scalars().all()
    
    output = []
    for c in challenges:
        # Get creator
        result = await db.execute(select(User).where(User.id == c.creator_id))
        creator = result.scalar_one_or_none()
        
        # Get participant count
        p_count_res = await db.execute(select(func.count(ChallengeParticipant.user_id)).where(ChallengeParticipant.challenge_id == c.id))
        p_count = p_count_res.scalar()
        
        # Check if current user is participant
        joined_res = await db.execute(select(ChallengeParticipant).where(
            and_(ChallengeParticipant.challenge_id == c.id, ChallengeParticipant.user_id == current_user.id)
        ))
        is_joined = joined_res.scalar_one_or_none() is not None
        
        output.append({
            "id": str(c.id),
            "title": c.title,
            "type": c.type,
            "targetValue": c.target_value,
            "currentValue": 0, # In a real app, this would aggregate logs for the challenge type
            "participants": p_count,
            "daysLeft": c.days, 
            "creatorName": creator.username if creator else "YASHA",
            "isCreator": c.creator_id == current_user.id,
            "isJoined": is_joined
        })
    return output

@router.post("/challenges/{challenge_id}/join")
async def join_challenge(challenge_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Check if exists
    challenge = await db.get(Challenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Chellenj topilmadi")
    
    # Check if already joined
    res = await db.execute(select(ChallengeParticipant).where(
        and_(ChallengeParticipant.challenge_id == challenge_id, ChallengeParticipant.user_id == current_user.id)
    ))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Siz allaqachon qo'shilgansiz")
    
    participant = ChallengeParticipant(challenge_id=challenge_id, user_id=current_user.id)
    db.add(participant)
    await db.commit()
    return {"status": "success"}

@router.get("/referrals")
async def get_my_referrals(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get user's referral stats and list"""
    import os
    
    # 1. Ensure referral code exists
    if not current_user.referral_code:
        # Generate one (simple logic: r + id)
        current_user.referral_code = f"r{current_user.id}"
        await db.commit()
    
    # 2. Get referrers
    res = await db.execute(select(User).where(User.referrer_id == current_user.id).order_by(desc(User.created_at)))
    referrers = res.scalars().all()
    
    # 3. Format
    refs_list = []
    for r in referrers:
        refs_list.append({
            "id": r.id,
            "name": r.full_name or r.username or f"User {r.id}",
            "date": r.created_at.strftime("%Y-%m-%d"),
            "points": 1 # Hardcoded +1 per referral as per rules
        })
        
    bot_username = os.getenv("BOT_USERNAME", "yashabot")
    
    return {
        "code": current_user.referral_code,
        "link": f"https://t.me/{bot_username}?start={current_user.referral_code}",
        "total_invited": len(refs_list),
        "total_earned": len(refs_list) * 1, # Provided 1 point per referral mostly
        "referrals": refs_list
    }
