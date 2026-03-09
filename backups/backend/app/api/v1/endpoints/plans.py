from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models import User, Plan
from backend.app.api.v1.endpoints.users import get_current_user
from backend.app.services.ai_service import ai_service
import json
import os
import random

router = APIRouter()

def load_template(category: str, template_id: str):
    """Load template from JSON file"""
    template_path = os.path.join("templates", category, f"{template_id}.json")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

@router.post("/workout")
async def generate_workout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate workout plan - template for free, AI for premium"""
    
    if not current_user.is_premium:
        # Return random template for free users
        templates = ["beginner_home", "weight_loss", "muscle_gain"]
        template_id = random.choice(templates)
        template = load_template("workouts", template_id)
        
        if not template:
            raise HTTPException(status_code=500, detail="Template not found")
        
        return {
            "plan": template["plan"],
            "is_premium": False,
            "type": "template",
            "template_name": template["name"],
            "upgrade_message": "💎 Individual AI reja uchun Premium obuna oling!"
        }
    
    # Generate AI plan for premium users
    prompt = f"""
    Create a 4-day workout plan for {current_user.age} year old {current_user.gender}.
    Goal: {current_user.goal}.
    Format: Bold headers, bullet points, no HTML.
    """
    
    raw_text = ai_service.generate_content(prompt)
    formatted = ai_service.format_text(raw_text, "Haftalik Mashq Rejasi")
    
    plan = Plan(user_id=current_user.id, type="workout", content=formatted)
    db.add(plan)
    await db.commit()
    
    return {
        "plan": formatted,
        "is_premium": True,
        "type": "ai"
    }

@router.post("/meal")
async def generate_meal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate meal plan - template for free, AI for premium"""
    
    if not current_user.is_premium:
        # Return random template for free users
        templates = ["meal_1500", "meal_2000", "meal_2500"]
        template_id = random.choice(templates)
        template = load_template("meals", template_id)
        
        if not template:
            raise HTTPException(status_code=500, detail="Template not found")
        
        return {
            "plan": template["plan"],
            "is_premium": False,
            "type": "template",
            "template_name": template["name"],
            "upgrade_message": "💎 Individual AI reja uchun Premium obuna oling!"
        }
    
    # Generate AI plan for premium users
    allergy_note = ""
    if current_user.allergies:
        allergy_note = f"\n⚠️ MUHIM: Foydalanuvchida {current_user.allergies} ga allergiya bor!"
    
    prompt = f"""
    Create a 7-day meal plan for {current_user.age} year old {current_user.gender}.
    Goal: {current_user.goal}. Uzbek cuisine.{allergy_note}
    Format: Bold headers, bullet points, no HTML.
    """
    
    raw_text = ai_service.generate_content(prompt)
    formatted = ai_service.format_text(raw_text, "Haftalik Ovqat Rejasi")
    
    plan = Plan(user_id=current_user.id, type="meal", content=formatted)
    db.add(plan)
    await db.commit()
    
    return {
        "plan": formatted,
        "is_premium": True,
        "type": "ai"
    }

