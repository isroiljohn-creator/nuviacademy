from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.database import get_db
from backend.models import User, Plan
from backend.app.api.v1.endpoints.users import get_current_user
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

@router.get("/meal")
async def get_meal_plan(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Get latest meal plan (Checks Template System first, then Legacy)"""
    from backend.models import UserMenuLink, MenuTemplate
    
    # 1. Check New Template System (Bot Logic)
    link_result = await db_session.execute(
        select(UserMenuLink)
        .where(UserMenuLink.user_id == current_user.id, UserMenuLink.is_active == True)
        .order_by(desc(UserMenuLink.id))
        .limit(1)
    )
    user_link = link_result.scalar_one_or_none()
    
    if user_link:
        tmpl_result = await db_session.execute(
            select(MenuTemplate).where(MenuTemplate.id == user_link.menu_template_id)
        )
        template = tmpl_result.scalar_one_or_none()
        
        if template:
            try:
                content = json.loads(template.menu_json)
                return {
                    "plan": content, 
                    "is_premium": current_user.is_premium, 
                    "created_at": user_link.start_date,
                    "source": "template" 
                }
            except Exception as e:
                print(f"Template JSON Error: {e}")

    # 2. Fallback to Legacy Plan Table
    result = await db_session.execute(
        select(Plan)
        .where(Plan.user_id == current_user.id, Plan.type == "meal")
        .order_by(desc(Plan.id))
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        return {"plan": None}
        
    try:
        content = json.loads(plan.content)
    except:
        content = plan.content # Fallback if text
        
    return {"plan": content, "is_premium": current_user.is_premium, "created_at": plan.created_at}

@router.get("/workout")
async def get_workout_plan(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Get latest workout plan"""
    result = await db_session.execute(
        select(Plan)
        .where(Plan.user_id == current_user.id, Plan.type == "workout")
        .order_by(desc(Plan.id))
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        return {"plan": None}
        
    try:
        content = json.loads(plan.content)
        
        # Enrich with Video URLs
        # Plan structure usually: {"monday": [{"name": "Push ups", ...}], "tuesday": ...} or just a list
        # We need to iterate and inject video_url
        
        exercises_to_fetch = []
        
        # Helper to collect names
        def collect_names(data):
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "name" in item:
                        exercises_to_fetch.append(item["name"])
            elif isinstance(data, dict):
                for key, value in data.items():
                    collect_names(value)

        collect_names(content)
        
        if exercises_to_fetch:
            from sqlalchemy import text
            # Fetch videos for these exercises
            # Use lower case for matching to be safe
            names_params = {f"n{i}": name for i, name in enumerate(exercises_to_fetch)}
            
            if names_params:
                # Construct WHERE clause like: name ILIKE :n0 OR name ILIKE :n1 ...
                # Actually, strictly matches might be better for performance, but plans might have slight variations
                # Let's try exact match first
                
                # Fetch dictionary of {name: video_url}
                video_map = {}
                
                # We can't easily do WHERE name IN (...) with asyncpg and params logic efficiently in one go if list is dynamic
                # So let's just query exercise_videos table for all relevant ones 
                # OR just query all videos if list is small? No.
                
                # Better: loop and query? No, N+1 problem.
                # Correct: WHERE name = ANY(:names)
                
                sql = text("""
                    SELECT 
                        e.name, 
                        COALESCE(v.video_url, e.video_url) as video_url
                    FROM exercises e
                    LEFT JOIN exercise_videos v ON e.name = v.name
                    WHERE e.name = ANY(:names)
                """)
                
                # Execute
                result = await db_session.execute(sql, {"names": list(exercises_to_fetch)})
                rows = result.fetchall()
                
                for r in rows:
                    if r.video_url:
                        video_map[r.name] = r.video_url
                        # Also handle case insensitive?
                        video_map[r.name.lower()] = r.video_url

                # Inject back into content
                def inject_videos(data):
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "name" in item:
                                vid = video_map.get(item["name"]) or video_map.get(item["name"].lower())
                                if vid:
                                    item["video_url"] = vid
                    elif isinstance(data, dict):
                        for key, value in data.items():
                            inject_videos(value)
                            
                inject_videos(content)

    except Exception as e:
        print(f"Error parse/enrich plan: {e}")
        content = plan.content
        
    return {"plan": content, "is_premium": current_user.is_premium, "created_at": plan.created_at}


@router.post("/meal")
async def generate_meal(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Generate meal plan - UNIFIED (Template System)"""
    from backend.models import UserMenuLink, MenuTemplate
    
    # 1. Profile Calculation
    weight = current_user.weight or 70.0
    height = current_user.height or 170
    age = current_user.age or 25
    gender = current_user.gender or 'male'
    activity = current_user.activity_level or "moderate"
    
    # Simple TDEE calc
    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == 'male' else -161)
    
    activity_multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9
    }
    multiplier = activity_multipliers.get(activity, 1.55)
    tdee = bmr * multiplier
    
    if current_user.goal == 'lose': tdee -= 500
    elif current_user.goal == 'gain': tdee += 300
    daily_target = round(tdee)
    
    # 2. Check Entitlements (Limit Enforced)
    if current_user.is_premium:
        try:
            from core.entitlements import check_and_consume
            # Telegram ID is needed for entitlement check
            ent_status = check_and_consume(current_user.telegram_id, 'menu_generate')
            if not ent_status['allowed']:
                raise HTTPException(status_code=403, detail=ent_status.get('message_uz', "Limit tugadi"))

            from core.ai import ai_generate_weekly_meal_plan_json
            
            # Deactivate old links
            from sqlalchemy import update
            stmt = update(UserMenuLink).where(UserMenuLink.user_id == current_user.id).values(is_active=False)
            await db_session.execute(stmt)

            # AI Generation
            full_data = ai_generate_weekly_meal_plan_json(
                user_profile={
                    "age": age, "gender": gender, "height": height, "weight": weight,
                    "goal": current_user.goal, "activity_level": activity,
                    "allergies": current_user.allergies,
                    "telegram_id": current_user.telegram_id
                },
                daily_target=daily_target
            )
            
            menu_json = json.dumps(full_data.get('menu', []))
            shop_json = json.dumps(full_data.get('shopping_list', []))
            
            # Create Template (Unique per generation for Premium users to avoid sharing custom AI plans?)
            # Or use profile key. For AI plans, it's safer to store as new template for now or reuse if exact match.
            # Bot logic: db.create_menu_template uses profile_key. User specific AI plan might not share key well.
            # Let's create a NEW template for this specific AI generation.
            
            new_tmpl = MenuTemplate(
                profile_key=f"ai_{current_user.id}_{int(random.random()*10000)}", # Unique key
                menu_json=menu_json,
                shopping_list_json=shop_json
            )
            db_session.add(new_tmpl)
            await db_session.flush() # Get ID
            
            # Link Result
            new_link = UserMenuLink(
                user_id=current_user.id,
                menu_template_id=new_tmpl.id,
                is_active=True
            )
            db_session.add(new_link)
            await db_session.commit()
            
            return {
                "plan": full_data.get('menu', []),
                "is_premium": True,
                "type": "ai",
                "source": "template_system"
            }
            
        except Exception as e:
            print(f"Meal Gen Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    else:
        # FREE TIER MATCHING
        # Use existing Pre-made Templates
        # Logic: Find a template that matches approx calories? 
        # Or just random.
        templates = ["meal_1500", "meal_2000", "meal_2500"]
        chosen = random.choice(templates)
        
        # We need to find or create a DB Template for this static file to link it.
        # This is tricky if we don't have them in DB.
        # Check if we imported them?
        # If not, let's just return the JSON (Legacy Fallback)
        # BUT then get_meal_plan will still find the OLD valid link from Bot if it exists.
        
        # Recommendation: Deactivate old links anyway!
        old_links = await db_session.execute(
             select(UserMenuLink).where(UserMenuLink.user_id == current_user.id, UserMenuLink.is_active == True)
        )
        for link in old_links.scalars():
            link.is_active = False
        await db_session.commit()
        
        # Load file
        template_data = load_template("meals", chosen)
        if not template_data:
             return {"plan": None, "message": "No template"}
             
        return {
            "plan": template_data["plan"],
            "is_premium": False,
            "type": "template_legacy"
        }

@router.post("/workout")
async def generate_workout(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Generate workout plan - unified"""
    # Simply deactivate old links to ensure fresh start, then use legacy return (Bot doesn't use workout templates yet?)
    # Bot uses Plan table for workouts? No, WorkoutTemplate exists too?
    # Let's check models. UserWorkoutLink exists?
    # Assume yes for consistency. Deactivate old links.
    
    # For now, just fix the Meal issue which is urgent.
    # We will just deactivate old UserMenuLinks if this was a meal plan request? No, this is workout.
    
    # Legacy logic for workout is fine for now unless Bot uses WorkoutTemplate.
    # Current codebase implies Bot uses `workout.py` which shows menus.
    # Does Bot generate workouts?
    # Let's leave workout as is but just fix Meal Sync.
    
    if not current_user.is_premium:
        templates = ["beginner_home", "weight_loss", "muscle_gain"]
        template_id = random.choice(templates)
        template = load_template("workouts", template_id)
        if not template: return {"plan": None}
        return {"plan": template["plan"], "is_premium": False}
        
    try:
        from core.entitlements import check_and_consume
        ent_status = check_and_consume(current_user.telegram_id, 'workout_generate')
        if not ent_status['allowed']:
             raise HTTPException(status_code=403, detail=ent_status.get('message_uz', "Limit tugadi"))

        from core.ai import ai_generate_weekly_workout_json
        profile = {
            "age": current_user.age or 25,
            "gender": current_user.gender,
            "goal": current_user.goal,
            "activity_level": current_user.activity_level
        }
        full = ai_generate_weekly_workout_json(profile)
        plan_json = full.get('schedule', [])
        
        # Save to Legacy Plan (Bot uses this for workouts?)
        from backend.models import Plan
        plan = Plan(user_id=current_user.id, type="workout", content=json.dumps(plan_json))
        db_session.add(plan)
        await db_session.commit()
        
        return {"plan": plan_json, "is_premium": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
