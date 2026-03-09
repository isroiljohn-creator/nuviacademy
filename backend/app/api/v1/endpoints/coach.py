from fastapi import APIRouter, Depends, HTTPException
from core.db import db
from core.coach import get_coach_message
from pydantic import BaseModel
from typing import List, Optional, Any
from backend.app.api.v1.endpoints.users import get_current_user
from backend.models import User
from core.ai import ask_gemini
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db

router = APIRouter()

class ChatMessage(BaseModel):
    id: str | int
    role: str
    content: str
    
class UserContext(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    goal: Optional[str] = None
    todayWater: Optional[int] = None
    todaySteps: Optional[int] = None
    todaySleep: Optional[float] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    userContext: Optional[UserContext] = None

@router.get("/today")
async def get_today_coach_message_api(user_id: int):
    """
    Get today's coach zone message for the Mini App home screen.
    """
    msg = get_coach_message(user_id)
    return {"message": msg}

@router.post("/chat")
async def chat_with_coach(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """
    AI Coach Chat Endpoint.
    Replaces Supabase Edge Function to provide AI advice based on context.
    """
    from core.entitlements import check_and_consume
    
    # Check entitlements before processing
    result = check_and_consume(current_user.telegram_id, 'ai_chat')
    if not result['allowed']:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "LIMIT_REACHED",
                "feature_key": "ai_chat",
                "plan": result['plan'],
                "limit": result['limit'],
                "used": result['used'],
                "reset_at": result['reset_at'].isoformat() if result['reset_at'] else None,
                "upgrade_to": result.get('upgrade_to'),
                "message_uz": result.get('message_uz')
            }
        )
    
    try:
        ctx = req.userContext
        user_message = ""
        history = ""
    
        # Take the last message as the current prompt
        if req.messages:
            last_msg = req.messages[-1]
            if last_msg.role == 'user':
                user_message = last_msg.content
            
            # Format previous messages as history
            recent_msgs = req.messages[:-1]
            if len(recent_msgs) > 10:
                recent_msgs = recent_msgs[-10:]
            
            for m in recent_msgs:
                role_label = "Foydalanuvchi" if m.role == 'user' else "AI Coach"
                history += f"{role_label}: {m.content}\n"

        if not user_message:
            return {"reply": "Tushunmadim, qaytadan yozing."}

        # 1. [FAQ ENGINE] Check Database First (This is FREE and doesn't consume AI limits)
        try:
            from core.qa_engine import get_best_match
            db_match = get_best_match(user_message, threshold=0.75) # Higher threshold for strict FAQ
            
            if db_match:
                return {
                    "reply": db_match['match']['answer'],
                    "source": "knowledge_base"
                }
        except Exception as e:
            print(f"QA Engine Error: {e}")

        # 2. Check Entitlements BEFORE calling AI
        from core.entitlements import check_and_consume
        limit_result = check_and_consume(current_user.telegram_id, 'ai_chat')
        
        if not limit_result['allowed']:
            # Return structured error that frontend can handle or just show the message_uz
            return {
                "reply": limit_result.get('message_uz', "Limitingiz tugadi."),
                "error": "LIMIT_REACHED",
                "upgrade_to": limit_result.get('upgrade_to')
            }

        # 3. AI Generation
        context_str = ""
        if ctx:
            context_str = f"""
Foydalanuvchi ma'lumotlari:
Ism: {ctx.name or current_user.full_name}
Yosh: {ctx.age or current_user.age}
Maqsad: {ctx.goal or current_user.goal}
Bugungi natijalar:
- Suv: {ctx.todayWater} ml
- Qadamlar: {ctx.todaySteps}
- Uyqu: {ctx.todaySleep} soat
"""

        system_prompt = f"""
Siz YASHA - professional sog'lom turmush tarzi va fitness murabbiyisiz.
Sizning vazifangiz foydalanuvchiga motivatsiya berish, ovqatlanish va mashg'ulotlar bo'yicha maslahat berish.
Javoblaringiz qisqa, lunda va FAQAT o'zbek tilida (lotin alifbosida) bo'lsin.
Emotsional va do'stona gapiring.

{context_str}

Suhbat tarixi:
{history}
"""
        response_text = ask_gemini(system_prompt, user_message, user_id=current_user.telegram_id, feature="ai_chat")
        
        if not response_text:
             raise Exception("AI empty response")

        # 4. [LEARNING] Save to KnowledgeBase for future reuse
        try:
            from core.qa_engine import save_to_knowledge_base
            save_to_knowledge_base(user_message, response_text, topic=ctx.goal if ctx else "General")
        except Exception as le:
            print(f"Learning Error: {le}")

        return {
            "reply": response_text,
            "source": "ai_gemini"
        }

    except Exception as e:
        print(f"Chat Error: {e}")
        # Fail gracefully
        return {
            "reply": "Uzr, hozircha javob bera olmayman. Iltimos, bir ozdan so'ng qayta urining.",
            "error": str(e)
        }

