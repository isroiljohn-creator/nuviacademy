from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models import Exercise

router = APIRouter()

@router.get("/exercises")
async def get_exercises(db: AsyncSession = Depends(get_db)):
    """Fetch all exercises for the library."""
    result = await db.execute(select(Exercise).order_by(Exercise.category, Exercise.name))
    exercises = result.scalars().all()
    
    return [
        {
            "id": e.id,
            "name": e.name,
            "video_url": e.video_url,
            "category": e.category,
            "difficulty": e.difficulty
        }
        for e in exercises
    ]

@router.get("/exercises_with_videos")
async def get_exercises_with_videos(db: AsyncSession = Depends(get_db)):
    """Fetch all exercises with video URLs using RAW SQL for reliability."""
    from sqlalchemy import text
    
    try:
        # Raw SQL query to bypass potential ORM mapping issues
        # Left join to get all exercises even if they don't have a video entry yet
        sql = text("""
            SELECT 
                e.id, 
                e.name, 
                e.category, 
                e.difficulty, 
                e.muscle_group, 
                e.equipment, 
                e.duration_sec, 
                e.description,
                COALESCE(v.video_url, e.video_url) as video_url,
                v.file_id
            FROM exercises e
            LEFT JOIN exercise_videos v ON e.name = v.name
            ORDER BY e.category, e.name
        """)

        
        result = await db.execute(sql)
        rows = result.fetchall()
        
        exercises_data = []
        for row in rows:
            exercises_data.append({
                "id": row.id,
                "name": row.name,
                "category": row.category or "other",
                "difficulty": row.difficulty or "beginner",
                "video_url": row.video_url,
                "file_id": row.file_id,
                "muscle_group": row.muscle_group or "",
                "equipment": row.equipment or "",
                "duration_sec": row.duration_sec or 60,
                "description": row.description or ""
            })
        
        if not exercises_data:
             print("WARNING: Raw SQL returned 0 exercises")
             
        return exercises_data
    except Exception as e:
        print(f"CRITICAL ERROR in get_exercises_with_videos: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list instead of 500 so frontend can show fallback
        return []


@router.get("/video_url")
async def get_video_url(exercise_name: str, db: AsyncSession = Depends(get_db)):
    """Fetch video URL for a given exercise. Returns from cache or fetches from YMove."""
    from backend.models import ExerciseVideo
    from sqlalchemy import select
    from core.ymove import search_video
    
    # 1. Check DB
    result = await db.execute(
        select(ExerciseVideo).where(ExerciseVideo.name.ilike(f"%{exercise_name}%"))
    )
    video = result.scalar_one_or_none()
    
    if video and video.video_url:
        return {"video_url": video.video_url, "source": "cache"}
    
    # 2. Fallback: Fetch from YMove
    try:
        ymove_data = search_video(exercise_name)
        if ymove_data and ymove_data.get('videoUrl'):
            video_url = ymove_data['videoUrl']
            
            # Cache it for future (optional: also upload to Telegram via maintenance.cache_video_on_demand)
            # For now, just save the URL
            if video:
                video.video_url = video_url
            else:
                new_video = ExerciseVideo(
                    name=exercise_name,
                    file_id="pending",  # Placeholder
                    video_url=video_url,
                    ymove_id=ymove_data.get('uuid')
                )
                db.add(new_video)
            await db.commit()
            
            return {"video_url": video_url, "source": "ymove"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")
    
    raise HTTPException(status_code=404, detail="Video not found")

