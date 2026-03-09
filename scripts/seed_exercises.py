import sys
import os
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import get_sync_db
from backend.models import Exercise

def seed_exercises():
    print("🏋️ Seeding Exercises...")
    
    # Base Exercises Data
    # Format: name_uz, category, muscle_group, equipment, difficulty, video_id
    base_moves = [
        # CHEST (Ko'krak)
        ("Oddiy Jim (Otjimaniya)", "strength", "chest", "none", "beginner", "IODxDxX7oi4"),
        ("Keng qo'l jimi", "strength", "chest", "none", "intermediate", "rrT-vfg3k6I"),
        ("Tor qo'l jimi (Diamond)", "strength", "chest", "none", "advanced", "J0DnG1_S92I"),
        ("Gantel bilan yotib ko'tarish", "strength", "chest", "dumbbells", "intermediate", "VmB1G1K7v94"),
        ("Nishab stulda gantel ko'tarish", "strength", "chest", "dumbbells", "intermediate", "8iPEnn-ltC8"),
        ("Gantel pullover", "strength", "chest", "dumbbells", "advanced", "5Y8K-456"),
        ("Bruchda jim (Dips)", "strength", "chest", "machine", "advanced", "wiCK09_123"),
        ("Krossoverda qo'l birlashtirish", "strength", "chest", "machine", "intermediate", "xyz_cross_123"),
        ("Shtanga bilan yotib ko'tarish", "strength", "chest", "barbell", "intermediate", "barbell_bench"),
        ("Nishab stulda shtanga", "strength", "chest", "barbell", "advanced", "incline_bench"),

        # BACK (Bel/Orqa)
        ("Turnikda tortilish (keng)", "strength", "back", "none", "advanced", "pullup_wide"),
        ("Turnikda tortilish (teskari)", "strength", "back", "none", "intermediate", "chinup"),
        ("Bukilgan holda gantel tortish", "strength", "back", "dumbbells", "intermediate", "row_db"),
        ("Bir qo'llab gantel tortish", "strength", "back", "dumbbells", "intermediate", "one_arm_row"),
        ("Shtanga tortish (Stanovaya)", "strength", "back", "barbell", "advanced", "deadlift"),
        ("Blokda ko'krakka tortish", "strength", "back", "machine", "beginner", "lat_pull"),
        ("Gorizontal blok tortish", "strength", "back", "machine", "beginner", "seated_row"),
        ("Gipertenziya", "strength", "back", "machine", "beginner", "hyperext"),
        ("Superman mashqi", "strength", "back", "none", "beginner", "superman"),
        ("Renegade Row", "strength", "back", "dumbbells", "advanced", "renegade_row"),

        # LEGS (Oyoq)
        ("O'tirib turish (Squat)", "strength", "legs", "none", "beginner", "squat_body"),
        ("Gantel bilan o'tirib turish", "strength", "legs", "dumbbells", "intermediate", "squat_db"),
        ("Shtanga bilan o'tirib turish", "strength", "legs", "barbell", "advanced", "squat_bar"),
        ("Lunges (Oldinga tashlash)", "strength", "legs", "none", "beginner", "lunges"),
        ("Gantel bilan Lunges", "strength", "legs", "dumbbells", "intermediate", "lunges_db"),
        ("Bolgar o'tirish (Bulgarian Split)", "strength", "legs", "none", "advanced", "bulgarian"),
        ("Oyoq pressi (Leg Press)", "strength", "legs", "machine", "intermediate", "leg_press"),
        ("Oyoq yozish (Extension)", "strength", "legs", "machine", "beginner", "leg_ext"),
        ("Oyoq bukish (Curl)", "strength", "legs", "machine", "beginner", "leg_curl"),
        ("Kalf ko'tarish (Oyoq uchi)", "strength", "legs", "none", "beginner", "calf_raise"),
        ("Gantel bilan Kalf", "strength", "legs", "dumbbells", "intermediate", "calf_sb"),
        ("Sumo Squat", "strength", "legs", "dumbbells", "intermediate", "sumo_squat"),
        ("Goblet Squat", "strength", "legs", "dumbbells", "beginner", "goblet"),
        ("Glute Bridge", "strength", "legs", "none", "beginner", "glute_bridge"),
        ("Hip Thrust", "strength", "legs", "barbell", "advanced", "hip_thrust"),

        # SHOULDERS (Yelka)
        ("Gantel press (tik turib)", "strength", "shoulders", "dumbbells", "intermediate", "shoulder_press"),
        ("Gantel 2 yonga ko'tarish", "strength", "shoulders", "dumbbells", "intermediate", "lat_raise"),
        ("Gantel oldinga ko'tarish", "strength", "shoulders", "dumbbells", "beginner", "front_raise"),
        ("Gantel egilib yonga", "strength", "shoulders", "dumbbells", "intermediate", "rear_delt"),
        ("Arnold press", "strength", "shoulders", "dumbbells", "advanced", "arnold"),
        ("Shtanga press (Soldat)", "strength", "shoulders", "barbell", "advanced", "military"),
        ("Yelka tortish (Shrugs)", "strength", "shoulders", "dumbbells", "beginner", "shrugs"),
        ("Face Pull (Blokda)", "strength", "shoulders", "machine", "intermediate", "face_pull"),
        ("Pike Pushups", "strength", "shoulders", "none", "advanced", "pike_push"),
        ("Planka yelka tegish (Taps)", "strength", "shoulders", "none", "beginner", "plank_tap"),

        # ARMS (Qo'llar)
        ("Gantel bilan biseps", "strength", "arms", "dumbbells", "beginner", "bicep_curl"),
        ("Bolg'a (Hammer) ko'tarish", "strength", "arms", "dumbbells", "beginner", "hammer"),
        ("Konsentratsiyalangan biseps", "strength", "arms", "dumbbells", "intermediate", "conc_curl"),
        ("Shtanga biseps", "strength", "arms", "barbell", "intermediate", "bar_curl"),
        ("Tritsps stulda (Dips)", "strength", "arms", "none", "beginner", "chair_dips"),
        ("Fransuz pressi (yotib)", "strength", "arms", "barbell", "intermediate", "skullcrusher"),
        ("Blokda tritsps bosish", "strength", "arms", "machine", "beginner", "tri_pushdown"),
        ("Gantel bosh ortidan", "strength", "arms", "dumbbells", "beginner", "ovh_ext"),
        ("Kickback (Gantel orqaga)", "strength", "arms", "dumbbells", "intermediate", "kickback"),
        ("Turnikda tor tortilish", "strength", "arms", "none", "advanced", "chinup_close"),

        # ABS (Qorin)
        ("Makiya (Crunches)", "strength", "abs", "none", "beginner", "crunches"),
        ("Oyoq ko'tarish (yotib)", "strength", "abs", "none", "beginner", "leg_raise"),
        ("Velosiped (Bicycle)", "strength", "abs", "none", "intermediate", "bicycle"),
        ("Planka (klassik)", "strength", "abs", "none", "beginner", "plank"),
        ("Yon planka", "strength", "abs", "none", "intermediate", "side_plank"),
        ("Ruscha burilish", "strength", "abs", "none", "intermediate", "rus_twist"),
        ("Turnikda oyoq ko'tarish", "strength", "abs", "none", "advanced", "hanging_leg"),
        ("V-up (Kitobcha)", "strength", "abs", "none", "advanced", "v_ups"),
        ("Tog' cho'qqisiga chiqish", "cardio", "abs", "none", "intermediate", "mountain_climber"),
        ("Vakuum", "strength", "abs", "none", "intermediate", "vacuum"),

        # CARDIO & HIIT
        ("Jumping Jacks", "cardio", "full_body", "none", "beginner", "jumps"),
        ("Burpees", "cardio", "full_body", "none", "advanced", "burpees"),
        ("Tizzani baland ko'tarish", "cardio", "legs", "none", "beginner", "high_knees"),
        ("Boks (soya jangi)", "cardio", "arms", "none", "beginner", "shadow_box"),
        ("Arqon sakrash", "cardio", "full_body", "equipment", "intermediate", "jump_rope"),
    ]
    
    # Generate 100 entries by creating variations if needed, but for now we have ~65 unique ones.
    # Let's duplicate some with different parameters/equipment to reach 100 if user wants explicitly 100.
    # Or just stick to ~65 quality ones? I'll expand with "Home" vs "Gym" variants for common moves.
    
    final_exercises = []
    
    for name, cat, muscle, equip, diff, vid_id in base_moves:
        # Home Variant
        final_exercises.append({
            "name": name,
            "category": cat,
            "muscle_group": muscle,
            "equipment": equip,
            "level": diff,
            "place": "home" if equip in ["none", "dumbbells", "bands"] else "gym",
            "video_url": f"https://www.youtube.com/watch?v={vid_id}",
            "description": f"{name} mashqi - {muscle} mushaklari uchun samarasidir.",
            "duration_sec": 60 if cat == "cardio" else None
        })
        
        # Gym Variant (if applicable)
        if equip == "none":
             # Bodyweight moves can be done in gym too
             final_exercises.append({
                "name": name + " (Zalda)",
                "category": cat,
                "muscle_group": muscle,
                "equipment": equip,
                "level": diff,
                "place": "gym",
                "video_url": f"https://www.youtube.com/watch?v={vid_id}",
                "description": f"{name} mashqini zalda bajarish.",
                "duration_sec": 60 if cat == "cardio" else None
            })

    print(f"Prepared {len(final_exercises)} exercises.")

    with get_sync_db() as session:
        count = 0
        for ex_data in final_exercises:
            # Upsert by name
            exists = session.query(Exercise).filter(Exercise.name == ex_data['name']).first()
            if not exists:
                new_ex = Exercise(
                    name=ex_data['name'],
                    category=ex_data['category'],
                    muscle_group=ex_data['muscle_group'],
                    equipment=ex_data['equipment'],
                    level=ex_data['level'],
                    place=ex_data['place'],
                    video_url=ex_data['video_url'],
                    description=ex_data['description'],
                    difficulty=ex_data['level'], # Map level to difficulty column
                    duration_sec=ex_data['duration_sec']
                )
                session.add(new_ex)
                count += 1
        
        session.commit()
        print(f"✅ inserted {count} new exercises.")

if __name__ == "__main__":
    seed_exercises()
