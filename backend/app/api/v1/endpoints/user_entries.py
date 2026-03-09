from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.app.api.v1.endpoints.users import get_current_user
from backend.models import User
from core.db import Database
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
db_helper = Database()

class MealEntry(BaseModel):
    name: str
    calories: int
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    meal_type: str # breakfast, lunch, dinner, snack
    date: str

class ExerciseEntry(BaseModel):
    name: str
    duration: int
    calories_burned: int
    date: str

@router.post("/meals")
async def add_meal(meal: MealEntry, current_user: User = Depends(get_current_user)):
    db_helper.save_meal_log(
        user_id=current_user.id,
        name=meal.name,
        calories=meal.calories,
        protein=meal.protein,
        carbs=meal.carbs,
        fat=meal.fat,
        meal_type=meal.meal_type,
        date=meal.date
    )
    return {"status": "success"}

@router.get("/meals/{date}")
async def get_meals(date: str, current_user: User = Depends(get_current_user)):
    logs = db_helper.get_meal_logs(current_user.id, date)
    return logs

@router.post("/workouts")
async def add_workout(workout: ExerciseEntry, current_user: User = Depends(get_current_user)):
    db_helper.save_exercise_log(
        user_id=current_user.id,
        name=workout.name,
        duration=workout.duration,
        calories_burned=workout.calories_burned,
        date=workout.date
    )
    return {"status": "success"}

@router.get("/workouts/{date}")
async def get_workouts(date: str, current_user: User = Depends(get_current_user)):
    logs = db_helper.get_exercise_logs(current_user.id, date)
    return logs

class WaterEntry(BaseModel):
    amount: int  # ml to add

class StepsEntry(BaseModel):
    steps: int   # steps to add

@router.post("/water")
async def add_water_entry(entry: WaterEntry, current_user: User = Depends(get_current_user)):
    total = db_helper.log_water(current_user.id, entry.amount)
    return {"status": "success", "total": total}

@router.post("/steps")
async def add_steps_entry(entry: StepsEntry, current_user: User = Depends(get_current_user)):
    total = db_helper.log_steps(current_user.id, entry.steps)
    return {"status": "success", "total": total}
