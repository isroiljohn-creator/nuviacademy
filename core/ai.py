import os
import json
import logging
import time
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
from core.db import db
from core.flags import is_flag_enabled
from core.menu_assembly import assemble_menu_7day
from core.workout_selector import select_workout_plan

logger = logging.getLogger("CoreAI")

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        # Configurable model with fallback
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        print(f"DEBUG: Gemini AI initialized successfully using {model_name}.")
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
else:
    print("DEBUG: GEMINI_API_KEY not found in environment variables.")

def get_micro_advice(menu_data, user_profile, lang="uz", user_id=None, return_usage=False):
    """AI generates only 1-2 motivating sentences for the menu."""
    goal = user_profile.get('goal', 'Sog‘liq')
    target = user_profile.get('kcal_target', 'hisoblanmoqda')
    
    # ... prompt logic ...
    prompt = f"""
    Siz professional diyetologsiz. Quyidagi menyu foydalanuvchi uchun tayyorlandi:
    Maqsad: {goal}
    Tayyorlangan kkal: {target}
    
    Faqat 1-2 ta juda qisqa va motivatsion gap yozing (lotin alifbosida, o'zbek tilida).
    Foydalanuvchiga 'SIZ' deb murojaat qiling.
    """
    if lang == 'ru':
        prompt = f"""
        Вы профессиональный диетолог. План питания готов.
        Цель: {goal}
        Ккал: {target}
        Напишите 1-2 коротких мотивирующих предложения на русском языке.
        Обращайтесь к пользователю на 'ВЫ'.
        """
        
    fallback_msg = "Sizga muvaffaqiyat tilayman! Rejaga amal qiling." if lang == 'uz' else "Желаю успеха! Придерживайтесь плана."
    try:
        if return_usage:
            advice, usage = ask_gemini("Diyetolog kabi qisqa motivatsiya beruvchi.", prompt, user_id=user_id, feature="menu_advice", return_usage=True)
            return (advice.strip() if advice else fallback_msg), usage
        else:
            advice = ask_gemini("Diyetolog kabi qisqa motivatsiya beruvchi.", prompt, user_id=user_id, feature="menu_advice")
            return advice.strip() if advice else fallback_msg
    except Exception as e:
        print(f"Error in get_micro_advice: {e}")
        if return_usage:
            return fallback_msg, {"input": 0, "output": 0, "cost": 0}
        return fallback_msg

def generate_workout_motivation_uz(user_profile, plan_summary):
    """
    AI is allowed ONLY for short motivation text (1–2 sentences, Uzbek, “SIZ” address).
    Returns (motivation_text, usage_dict).
    """
    goal = user_profile.get('goal', 'sog‘liq')
    user_id = user_profile.get('telegram_id') or user_profile.get('id')
    
    prompt = f"""
    Siz professional fitness murabbiysiz.
    Foydalanuvchi maqsadi: {goal}.
    Mashq rejasi haqida qisqacha ma'lumot: {plan_summary}
    
    Foydalanuvchiga 1-2 gaplik juda qisqa motivatsiya yozing.
    FAQAT O‘ZBEK TILIDA.
    Foydalanuvchiga 'SIZ' deb murojaat qiling.
    Maksimal 1 ta emoji ishlating.
    Tibbiy maslahat bermang.
    """
    
    try:
        # Using ask_gemini with restricted feature
        response, usage = ask_gemini("Motivatsion murabbiy", prompt, user_id=user_id, feature="workout_motivation", return_usage=True)
        if response:
            # Clean up potential markdown or quotes
            motivation = response.strip().strip('"').strip("'")
            return motivation, usage
    except Exception as e:
        logger.error(f"Motivation generation failed: {e}")
        
    return "Mashg'ulotlarni boshlashga tayyormisiz? Sizning intilishingiz natija garovidir!", {"input": 0, "output": 0, "cost": 0}

def get_offline_workout(user_profile, lang="uz"):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
    if lang == 'ru':
         header = f"⚠️ <b>AI сейчас занят, {name}!</b>\nНо я подготовил офлайн-план для вашей цели ({goal}):"
    else:
         header = f"⚠️ <b>AI hozircha band, {name}!</b>\nAmmo sizning maqsadingiz ({goal}) uchun maxsus offline rejani tayyorlab berdim:"
    
    if "Ozish" in goal or "weight_loss" in goal or "Vazn tashlash" in goal:
        return f"""{header}

<b>Dushanba (Butun tana):</b>
1. Yugurish (15 daqiqa)
2. O‘tirib turish (Squats) - 3x15
3. Jim yotib gantel ko‘tarish - 3x12
4. Plank - 3x45 soniya

<b>Chorshanba (Kardio + Press):</b>
1. Arqon sakrash - 10 daqiqa
2. Velosiped mashqi (press) - 3x20
3. Burpee - 3x10
4. Oyoq ko‘tarish (turnikda) - 3x12

<b>Juma (Oyoq va Yelka):</b>
1. Zina mashqi (10 daqiqa)
2. Lunges (Odimlash) - 3x15
3. Yelka pressi - 3x12
4. Yon tomonga gantel ko‘tarish - 3x15
"""
    elif "Massa" in goal or "muscle_gain" in goal or "Vazn olish" in goal:
        return f"""{header}

<b>Dushanba (Ko‘krak va Triceps):</b>
1. Jim yotib shtanga ko‘tarish - 4x8-10
2. Brusda ishlash - 3xMax
3. Gantel bilan pulover - 3x12
4. Triceps blokda - 3x12

<b>Chorshanba (Orqa va Biceps):</b>
1. Turnikda tortilish - 3xMax
2. Shtanga tortish (belga) - 4x8-10
3. Biceps shtanga - 3x10
4. Hammer (bolg‘a) usuli - 3x12

<b>Juma (Oyoq va Yelka):</b>
1. Shtanga bilan o‘tirib turish - 4x8-10
2. Oyoq pressi - 3x12
3. Yelka pressi (shtanga) - 3x10
4. Trapetsiya (shrugs) - 3x15
"""
    else: # Sog'liq / Umumiy
        return f"""{header}

<b>Dushanba:</b>
1. Yengil yugurish - 10 daqiqa
2. O‘tirib turish - 3x12
3. Otjimaniya - 3x10
4. Press mashqi - 3x15

<b>Chorshanba:</b>
1. Tez yurish - 20 daqiqa
2. Turnikda osilish - 3x30 soniya
3. Planka - 3x30 soniya
4. Cho‘zilish mashqlari

<b>Juma:</b>
1. Velosiped yoki Ellips - 15 daqiqa
2. Yengil gantel mashqlari - 3x12
3. Bel mashqlari (Gipertenziya) - 3x12
4. Nafas mashqlari
"""

def get_offline_menu(user_profile, lang="uz"):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
    if lang == 'ru':
        header = f"⚠️ <b>AI сейчас занят, {name}!</b>\nНо я подготовил офлайн-меню для вашей цели ({goal}):"
    else:
        header = f"⚠️ <b>AI hozircha band, {name}!</b>\nAmmo sizning maqsadingiz ({goal}) uchun maxsus offline rejani tayyorlab berdim:"
    
    if "Ozish" in goal or "weight_loss" in goal or "Vazn tashlash" in goal:
        return f"""{header}

<b>Nonushta:</b>
- 2 ta qaynatilgan tuxum
- Yarimta avokado yoki 10 ta bodom
- Ko‘k choy (shakarsiz)

<b>Tushlik:</b>
- 150g tovuq ko‘krak go‘shti (qaynatilgan)
- Grechka (yog‘siz)
- Karam va sabzi salati

<b>Kechki ovqat:</b>
- 150g baliq yoki tvorog
- Yashil sabzavotlar
- 1 stakan kefir
"""
    elif "Massa" in goal or "muscle_gain" in goal or "Vazn olish" in goal:
        return f"""{header}

<b>Nonushta:</b>
- 3 ta tuxum (qovurilgan)
- Suli yormasi (sut bilan, banan va asal qo‘shilgan)
- Tost non (pishloq bilan)

<b>Tushlik:</b>
- 200g mol go‘shti yoki tovuq
- Guruch yoki makaron
- Sabzavotli salat (zaytun moyi bilan)

<b>Kechki ovqat:</b>
- 150g baliq yoki tovuq
- Kartoshka pyure
- Tvorog (smetana bilan)
"""
    else:
        return f"""{header}

<b>Nonushta:</b>
- Suli yormasi (mevalar bilan)
- 1 ta qaynatilgan tuxum
- Choy yoki qahva

<b>Tushlik:</b>
- Tovuq sho‘rva
- 100g go‘sht va garnir
- Salat

<b>Kechki ovqat:</b>
- Yengil hazm bo‘ladigan taom (dimlama)
- Salat
- Olma yoki nok
"""

# Global Safety Settings
# Global Safety Settings (New SDK Format)
SAFETY_SETTINGS = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]

# Models to try in order
# Primary: from Env (default 1.5-flash)
# Fallback: versions with different suffixes to handle 404s in different regions/API versions
MODELS_TO_TRY = []
primary = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
MODELS_TO_TRY.append(primary)
fallbacks = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-1.5-flash-002", "gemini-1.5-flash-001"]
for fb in fallbacks:
    if fb not in MODELS_TO_TRY:
        MODELS_TO_TRY.append(fb)

def get_profile_key(profile):
    """Generates a cache key for deduplication."""
    age = int(profile.get('age', 25))
    age_band = f"{age // 5 * 5}-{(age // 5 * 5) + 4}"
    
    return f"{profile.get('gender')}|{profile.get('goal')}|{profile.get('activity_level')}|{profile.get('allergies')}|{age_band}|v6"

import threading
# Usage Stats (Thread-safe)
AI_USAGE_STATS = {
    "workout": 0,
    "meal": 0,
    "chat": 0,
    "vision": 0,
    "shopping": 0,
    "support": 0,
    "errors": 0,
    "total_requests": 0
}
AI_STATS_LOCK = threading.Lock()

def _increment_ai_stat(key):
    """Helper for thread-safe stat increment"""
    with AI_STATS_LOCK:
        if key in AI_USAGE_STATS:
            AI_USAGE_STATS[key] += 1
            if key != "errors":
                AI_USAGE_STATS["total_requests"] += 1

def ask_gemini(system_prompt, user_prompt, response_mime_type=None, response_schema=None, user_id=None, feature=None, return_usage=False):
    """
    Centralized helper to call Gemini with robust model fallback.
    Returns plain text response or raises Exception.
    Now includes structured logging for tokens and latency.
    """
    global client
    
    if not client:
        if not GEMINI_API_KEY:
            raise Exception("API Key topilmadi (GEMINI_API_KEY).")
        client = genai.Client(api_key=GEMINI_API_KEY)

    # Combine system and user prompt
    full_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
    
    last_error = None
    start_time = time.time()
    
    for model_name in MODELS_TO_TRY:
        try:
            print(f"DEBUG: Attempting AI generation with model: {model_name}")
            
            config_kwargs = {
                "safety_settings": SAFETY_SETTINGS,
                "max_output_tokens": 15000,
            }
            if response_mime_type:
                config_kwargs["response_mime_type"] = response_mime_type
            if response_schema:
                config_kwargs["response_schema"] = response_schema

            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            
            # latency
            latency_ms = (time.time() - start_time) * 1000

            if response.text:
                # Log usage if user_id is provided
                if user_id:
                    try:
                        usage = response.usage_metadata
                        input_tok = usage.prompt_token_count or 0
                        output_tok = usage.candidates_token_count or 0
                        total_tok = input_tok + output_tok
                        
                        # Pricing (Gemini 1.5 Flash estimate)
                        cost = (input_tok * 0.15 / 1000000) + (output_tok * 0.60 / 1000000)
                        
                        # 1. AI Usage Table
                        db.log_ai_usage_db(user_id, feature or "unknown", model_name, input_tok, output_tok, cost)
                        
                        # 2. Admin Events (as requested)
                        db.log_admin_event(
                            event_type="AI_TOKEN_USAGE",
                            user_id=user_id,
                            success=True,
                            latency_ms=latency_ms,
                            meta={
                                "feature": feature,
                                "model": model_name,
                                "input_tokens": input_tok,
                                "output_tokens": output_tok,
                                "total_tokens": total_tok,
                                "cost_usd": round(cost, 6)
                            }
                        )
                    except Exception as le:
                        print(f"Logging usage error: {le}")

                if return_usage:
                    usage = getattr(response, 'usage_metadata', None)
                    input_tok = usage.prompt_token_count or 0 if usage else 0
                    output_tok = usage.candidates_token_count or 0 if usage else 0
                    cost = (input_tok * 0.15 / 1000000) + (output_tok * 0.60 / 1000000)
                    return response.text.strip(), {"input": input_tok, "output": output_tok, "cost": cost}
                return response.text.strip()
            
        except Exception as e:
            err_str = str(e).lower()
            print(f"DEBUG: Model {model_name} failed: {e}")
            last_error = e
            
            # If it's a 404, we definitely want to try the next model
            if "404" in err_str or "not found" in err_str:
                continue
            
            # If it's a safety block, maybe try another model too
            if "finish_reason" in err_str and "safety" in err_str:
                continue
                
            # For other errors, keep trying until we run out of models
            continue
            
    # If all models fail
    print("ERROR: All AI models failed.")
    _increment_ai_stat("errors")
    
    # Log failure event
    if user_id:
        db.log_admin_event(
            event_type="AI_TOKEN_USAGE",
            user_id=user_id,
            success=False,
            meta={"feature": feature, "error": str(last_error)}
        )

    if return_usage:
        return None, {"input": 0, "output": 0, "cost": 0}
    # User friendly error
    raise Exception(f"AI tizimi bilan bog'lanishda xatolik yuz berdi. Iltimos, bir ozdan so'ng qayta urining. (Error: {last_error})")

def call_gemini(prompt):
    """Legacy wrapper for backward compatibility, redirects to ask_gemini"""
    try:
        return ask_gemini("You are a helpful assistant.", prompt)
    except Exception as e:
        print(f"DEBUG: call_gemini caught exception: {e}")
        return None

def ai_generate_workout(user_profile):
    """Generates a weekly workout plan using the robust unified logic."""
    return ai_generate_weekly_workout_json(user_profile)

def ai_generate_menu(user_profile):
    """Generates a weekly meal plan using the robust unified logic."""
    return ai_generate_weekly_meal_plan_json(user_profile)


MOCK_MENU_DATA = {
  "menu": [
    { "day": 1, "breakfast": "2 ta qaynatilgan tuxum, suli yormasi", "lunch": "Tovuq sho'rva, 1 tilim qora non", "dinner": "Dimlama (go'sht va sabzavotlar)", "snack": "1 ta olma" },
    { "day": 2, "breakfast": "Tvorog va smetana, ko'k choy", "lunch": "Moshkichiri, salat", "dinner": "Grill tovuq ko'krak qismi", "snack": "Bir hovuch yong'oq" },
    { "day": 3, "breakfast": "Omlet (2 tuxum, sut)", "lunch": "Mastava, qatiq", "dinner": "Baliq (duxovkada)", "snack": "Kefir" },
    { "day": 4, "breakfast": "Grechka sut bilan", "lunch": "Suyuq lag'mon", "dinner": "Sabzavotli salat va tovuq", "snack": "Apelsin" },
    { "day": 5, "breakfast": "Pishloqli buterbrod, kofe", "lunch": "No'xat shorva", "dinner": "Qaynatilgan mol go'shti, karam salat", "snack": "Quritilgan mevalar" }
  ],
  "shopping_list": [
    "Tuxum (10 dona)", "Tovuq go'shti (1 kg)", "Mol go'shti (0.5 kg)", "Baliq (0.5 kg)",
    "Suli yormasi", "Grechka", "Guruch", "Mosh",
    "Sabzavotlar (Kartoshka, Piyoz, Sabzi, Karam)", "Mevalar (Olma, Apelsin)",
    "Sut mahsulotlari (Tvorog, Smetana, Kefir, Sut)", "Non"
  ]
}





def ai_generate_weekly_meal_plan_json(user_profile, daily_target=2000, lang="uz", duration_weeks=1):
    """
    Generates a meal plan in JSON. 
    If duration_weeks > 1 (e.g. 4 for Pro), replicates the 1-week plan to fill the duration.
    """
    user_id = user_profile.get('telegram_id')
    
    # 1. Try DB Assembly first (Priority)
    start_time = time.time()
    source = "AI"
    is_fallback = False
    fallback_reason = None
    
    goal_tag = user_profile.get('goal', 'unknown')
    
    if is_flag_enabled("db_menu_assembly", user_id):
        try:
            db_plan_json = assemble_menu_7day(user_profile, daily_target)
            if db_plan_json:
                data = json.loads(db_plan_json)
                # Add micro-advice via AI
                advice, usage_adv = get_micro_advice(data, user_profile, lang=lang, user_id=user_id, return_usage=True) 
                data['micro_advice'] = advice
                source = "LOCAL"
                
                # Log Menu Generation Event
                latency_ms = (time.time() - start_time) * 1000
                db.log_admin_event(
                    event_type="MENU_GENERATION",
                    user_id=user_id,
                    success=True,
                    latency_ms=latency_ms,
                    meta={
                        "source": source,
                        "is_fallback": is_fallback,
                        "fallback_reason": fallback_reason,
                        "daily_target": daily_target,
                        "goal_tag": goal_tag,
                        "ai_input_tokens": usage_adv.get("input", 0),
                        "ai_output_tokens": usage_adv.get("output", 0),
                        "ai_total_tokens": usage_adv.get("input", 0) + usage_adv.get("output", 0),
                        "ai_cost_usd": usage_adv.get("cost", 0)
                    }
                )
                return data
            else:
                is_fallback = True
                fallback_reason = "db_assembly_returned_none"
        except Exception as e:
            logger.error(f"DB_MENU_ASSEMBLY_FAILED: {e}")
            is_fallback = True
            fallback_reason = f"db_assembly_exception: {str(e)}"
            # Fallback will continue to AI generation below
    
    _increment_ai_stat("meal")
    # ... legacy path usage collection ...
    # (Update AI path below)
    
    _increment_ai_stat("meal")

    # language context
    lang_instruction = "FAQAT O‘ZBEK TILI (LOTIN ALIFBOSIDA)."
    if lang == "ru":
        lang_instruction = "FAQAT RUS TILI (CYRILLIC). Respond strictly in Russian."

    # allergy_info
    allergy_text = user_profile.get('allergies')
    allergy_info = allergy_text if (allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']) else "Yo'q"

    # 1. System Prompt (Rich Nutritional Role)
    system_prompt = f"""
You are a professional Uzbek nutritionist, home chef, and supportive fitness coach.

Your task is to generate a 7-day meal plan in STRICT JSON format.

CONTEXT:
- Diet style: Oddiy o‘zbek uy ovqatlari
- Budget: Arzon / O‘rtacha
- Ingredients must be easily available in Uzbekistan
- Cooking skill: Boshlang‘ich
- Tone: Iliq, qo‘llab-quvvatlovchi, murabbiyona (insondek)

CRITICAL RULES (VERY IMPORTANT):

1. OUTPUT MUST BE VALID JSON ONLY. NO TEXT OUTSIDE JSON.
2. JSON STRUCTURE MUST NEVER CHANGE.
3. LANGUAGE: {lang_instruction} (Values must be in {lang}, but JSON Keys must be English matching the schema).
4. USERGA DOIM "{'SIZ' if lang == 'uz' else 'ВЫ'} DEB MUROJAAT QILING.

CALORIE RULES (STRICT):
- DAILY_TOTAL_KCAL MUST BE SUM OF MEALS.
- DAILY TOTAL MUST BE BETWEEN {daily_target-50} AND {daily_target+50}.
- EVERY MEAL MUST HAVE 'calories' (INTEGER).
- DAILY calories MUST BE LOGIC:
  - Nonushta: 25–30%
  - Tushlik: 35–40%
  - Kechki ovqat: 20–25%
  - Tamaddi: 5–10%

MEAL STRUCTURE (DO NOT CHANGE):
Each meal object MUST include:
- title (string)
- items (array of strings WITH QUANTITIES)
- recipe (string, tips or short context)
- steps (array of strings, step-by-step preparation)
- calories (integer)

SNACK (TAMADDI):
- MUST be an OBJECT
- title MUST be very short (2–3 words)
- calories is REQUIRED

SHOPPING LIST:
- Categorized into 'protein', 'veg', 'carbs', 'dairy', 'misc'
- TOTAL quantities for 7 DAYS.

DAILY OBJECT MUST INCLUDE:
- day (integer, 1-7)
- day_name (string, e.g. "Dushanba")
- meals (object containing breakfast, lunch, dinner, snack)
- total_calories (integer)

"""

    # 2. User Prompt (Context)
    user_prompt = f"""
Foydalanuvchi ma'lumotlari:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Maqsad: {user_profile.get('goal')}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik: {user_profile.get('activity_level', 'O’rtacha')}
Allergiya: {allergy_info}

VAZIFA: Menga 7 kunlik (Dushanba-Yakshanba) ovqatlanish rejasi kerak.
"""

    # -------------------------------------------------------------------------
    # HELPER: Safe JSON Generation with Retry/Repair
    # -------------------------------------------------------------------------
    def _generate_chunk(prompt_text, chunk_desc):
        print(f"DEBUG: Generating {chunk_desc}...")
        
        schema = {
            "type": "object",
            "properties": {
                "menu": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "integer"},
                            "day_name": {"type": "string"}, # Added day_name as per system prompt
                            "meals": {
                                "type": "object",
                                "properties": {
                                    "breakfast": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "calories": {"type": "integer"},
                                            "items": {"type": "array", "items": {"type": "string"}},
                                            "recipe": {"type": "string"},
                                            "steps": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["title", "calories", "items", "recipe", "steps"]
                                    },
                                    "lunch": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "calories": {"type": "integer"},
                                            "items": {"type": "array", "items": {"type": "string"}},
                                            "recipe": {"type": "string"},
                                            "steps": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["title", "calories", "items", "recipe", "steps"]
                                    },
                                    "dinner": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "calories": {"type": "integer"},
                                            "items": {"type": "array", "items": {"type": "string"}},
                                            "recipe": {"type": "string"},
                                            "steps": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["title", "calories", "items", "recipe", "steps"]
                                    },
                                    "snack": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "calories": {"type": "integer"},
                                            "items": {"type": "array", "items": {"type": "string"}},
                                            "recipe": {"type": "string"},
                                            "steps": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["title", "calories", "items", "recipe", "steps"]
                                    }
                                },
                                "required": ["breakfast", "lunch", "dinner", "snack"]
                            },
                            "total_calories": {"type": "integer"}
                        },
                        "required": ["day", "day_name", "meals", "total_calories"] # Added day_name to required
                    }
                },
                "shopping_list": {
                    "type": "object",
                    "properties": {
                        "protein": {"type": "array", "items": {"type": "string"}},
                        "veg": {"type": "array", "items": {"type": "string"}},
                        "carbs": {"type": "array", "items": {"type": "string"}},
                        "dairy": {"type": "array", "items": {"type": "string"}},
                        "misc": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["protein", "veg", "carbs", "dairy", "misc"]
                }
            },
            "required": ["menu", "shopping_list"]
        }

        try:
            # Use ask_gemini instead of direct client call for fallback
            # Pass user_id and feature for granular logging
            response_text, usage = ask_gemini(
                system_prompt, 
                prompt_text, 
                response_mime_type="application/json", 
                response_schema=schema,
                user_id=user_id,
                feature="menu",
                return_usage=True
            )
            
            if not response_text:
                raise Exception("Empty AI response")

            # Repair Logic (Compact)
            import re, json
            start_match = re.search(r'\{', response_text)
            clean_json = response_text[start_match.start():] if start_match else response_text
            clean_json = clean_json.split('```')[0].strip()
            
            try:
                 return json.loads(clean_json), usage
            except json.JSONDecodeError:
                 # Auto-repair common truncation
                 repaired = clean_json
                 if repaired.count('"') % 2 != 0: repaired += '"'
                 repaired += '}' * (repaired.count('{') - repaired.count('}'))
                 repaired += ']' * (repaired.count('[') - repaired.count(']'))
                 try:
                    return json.loads(repaired), usage
                 except:
                    # Trim last comma and try again
                    last_comma = clean_json.rfind(',')
                    if last_comma > 0:
                        repaired = clean_json[:last_comma]
                        repaired += '}' * (repaired.count('{') - repaired.count('}')) 
                        repaired += ']' * (repaired.count('[') - repaired.count(']'))
                        return json.loads(repaired), usage
                    raise
        except Exception as api_err:
            print(f"DEBUG: Chunk Generation error ({chunk_desc}): {api_err}")
            return {"menu": [], "shopping_list": {}}, {"input": 0, "output": 0, "cost": 0}

    # -------------------------------------------------------------------------
    # MAIN SPLIT LOGIC
    # -------------------------------------------------------------------------
    try:
        # 0. CACHE CHECK
        
        profile_key = get_profile_key(user_profile)
        cached = db.get_menu_template(profile_key)
        
        if cached:
            print(f"DEBUG: Cache Hit for Menu: {profile_key}")
            try:
                plan = json.loads(cached['menu_json'])
                shopping_list = json.loads(cached['shopping_list_json'])

                if not plan:
                    return None

                # --- Force Recalculate Daily Totals ---
                # AI often hallucinates the total sum. We must trust the individual meal calories more.
                total_week_cals = 0
                for day in plan:
                    d_sum = 0
                    if 'meals' in day:
                        for m_type in ['breakfast', 'lunch', 'dinner', 'snack']:
                            meal = day['meals'].get(m_type)
                            if meal and 'calories' in meal:
                                d_sum += int(meal['calories'])
                    
                    # Update the day's total to match the sum of meals
                    day['total_calories'] = d_sum
                    total_week_cals += d_sum

                # Replicate if needed
                if duration_weeks > 1:
                     original_plan = list(plan)
                     for w in range(1, duration_weeks):
                         for day_item in original_plan:
                             new_day = day_item.copy()
                             new_day['day'] = day_item['day'] + (7 * w)
                             plan.append(new_day)

                return {
                    "menu": plan,
                    "shopping_list": shopping_list
                }
            except Exception as e:
                 print(f"Cache Corrupt: {e}")

        base_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
        
        # PART 1: Days 1-3
        prompt_1 = base_prompt + "\n\n🚨 IMPORTANT TASK: Generate ONLY Days 1, 2, and 3. Return an EMPTY shopping_list for now."
        data_1, usage_1 = _generate_chunk(prompt_1, "Days 1-3")
        
        # PART 2: Days 4-7 + Shopping List
        prompt_2 = base_prompt + f"\n\n✅ Days 1-3 Generated. Now generate remaining.\n\n🚨 TASK: Generate ONLY Days 4, 5, 6, and 7. \nAND generate valid 'shopping_list' for THE WHOLE WEEK (Days 1-7)."
        data_2, usage_2 = _generate_chunk(prompt_2, "Days 4-7")
        
        # COMBINE
        plan = data_1.get('menu', []) if data_1 else [] 
        plan += data_2.get('menu', []) if data_2 else []
        shopping_list = data_2.get('shopping_list', {}) if data_2 else {}

        # Log Menu Generation Event (AI path)
        latency_ms = (time.time() - start_time) * 1000
        
        # Sum usage
        total_in = usage_1.get("input", 0) + usage_2.get("input", 0)
        total_out = usage_1.get("output", 0) + usage_2.get("output", 0)
        total_cost = usage_1.get("cost", 0) + usage_2.get("cost", 0)

        db.log_admin_event(
            event_type="MENU_GENERATION",
            user_id=user_id,
            success=True,
            latency_ms=latency_ms,
            meta={
                "source": source,
                "is_fallback": is_fallback,
                "fallback_reason": fallback_reason,
                "daily_target": daily_target,
                "goal_tag": goal_tag,
                "days_count": len(plan),
                "ai_input_tokens": total_in,
                "ai_output_tokens": total_out,
                "ai_total_tokens": total_in + total_out,
                "ai_cost_usd": total_cost
            }
        )

        if not plan:
            return None
        
        # Replicate for Pro users (Duration > 1 week)
        if duration_weeks > 1:
             original_plan = list(plan)
             for w in range(1, duration_weeks):
                 for day_item in original_plan:
                     new_day = day_item.copy()
                     new_day['day'] = day_item['day'] + (7 * w)
                     # Optional: Add note about repeating?
                     plan.append(new_day)
        
        merged_data = {
            "menu": plan,
            "shopping_list": shopping_list
        }
        
        # ROBUST CLEANING
        if "menu" in merged_data and isinstance(merged_data["menu"], list):
            for day in merged_data["menu"]:
                 if "meals" in day:
                     for meal_key in day["meals"]:
                         meal = day["meals"][meal_key]
                         if isinstance(meal, dict):
                             for field in ["title", "recipe"]:
                                 if field in meal and isinstance(meal[field], str):
                                     meal[field] = meal[field].replace(" tuzat", "").replace(" yoz", "").strip()
                                     if meal[field]:
                                         meal[field] = meal[field][0].upper() + meal[field][1:]

        # SAVE TO CACHE
        try:
             # Ensure it's valid data before saving
            if "menu" in merged_data and "shopping_list" in merged_data:
                 db.create_menu_template(
                     profile_key,
                     json.dumps(merged_data["menu"]),
                     json.dumps(merged_data["shopping_list"])
                 )
        except Exception as e:
             print(f"Cache Save Error: {e}")

        return merged_data
            
    except Exception as e:
        print(f"Split Generation Failed: {e}")
        raise e
        


def ai_answer_question(question, lang="uz"):
    """Answers a general fitness question using Gemini."""
    _increment_ai_stat("chat")
    
    prompt = f"Siz fitnes murabbiyisiz. Savolga qisqa va aniq javob bering (o'zbek tilida): {question}"
    if lang == 'ru':
        prompt = f"Вы фитнес-тренер. Ответьте на вопрос коротко и ясно (на русском): {question}"
        
    response_text = call_gemini(prompt)
    if response_text:
        title = "Javob" if lang != 'ru' else "Ответ"
        return format_gemini_text(response_text, title)
            
    return "⚠️ AI hozircha band. Iltimos, keyinroq urinib ko‘ring."

def ai_generate_shopping_list(user_profile, lang="uz"):
    """Generates a shopping list based on user profile and health context."""
    _increment_ai_stat("shopping")
    
    # Build allergy/health warning
    allergy_text = user_profile.get('allergies')
    health_context = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq', 'net']:
        health_context = f"\n⚠️ DIQQAT: Foydalanuvchida {allergy_text} ga allergiya bor. Ro'yxatga bularni qo'shmang!\n"
        if lang == 'ru':
            health_context = f"\n⚠️ ВНИМАНИЕ: У пользователя аллергия на {allergy_text}. Не добавляйте это!\n"
        
    prompt = f"""
    Foydalanuvchi maqsadi: {user_profile.get('goal')}
    {health_context}
    
    Vazifa: 3 kunlik sog'lom ovqatlanish uchun kerakli mahsulotlar ro'yxatini tuzing.
    
    📌 SHARTLAR:
    1. O'zbekiston bozorida oson topiladigan mahsulotlar bo'lsin (Bozor/Korzinka).
    2. Qimmat va kamyob narsalar (kinoa, avokado, losos) o'rniga mahalliy muqobillarini yozing.
    3. Agar allergiya bo'lsa, qat'iy inobatga oling.
    
    FORMAT:
    🛒 **Xaridlar Ro'yxati**
    
    **Sabzavot va Mevalar:**
    - ...
    
    **Oqsillar (Go'sht/Tuxum):**
    - ...
    
    **Don mahsulotlari:**
    - ...
    
    Qisqa va aniq bo'lsin.
    Muhim joylarni **qalin** qilib yoz.
    """
    
    if lang == 'ru':
        prompt = f"""
        Users Goal: {user_profile.get('goal')}
        {health_context}
        
        Task: Create a shopping list for 3 days of healthy eating.
        
        📌 RULES:
        1. Products must be easily found in Uzbekistan (Bazaar/Korzinka).
        2. Use local alternatives instead of expensive items (quinoa, avocado, salmon).
        3. STRICTLY respect allergies.
        
        FORMAT:
        🛒 **Список Покупок**
        
        **Овощи и Фрукты:**
        - ...
        
        **Белки (Мясо/Яйца):**
        - ...
        
        **Крупы:**
        - ...
        
        Keep it short and clear. Use **bold** for importance.
        Respond in RUSSIAN.
        """
    
    response = call_gemini(prompt)
    if response:
        title = "Xaridlar Ro'yxati" if lang != 'ru' else "Список Покупок"
        return format_gemini_text(response, title)
    return None

def analyze_food_image(image_data, lang="uz"):
    """
    Analyzes food image using Gemini Vision.
    Returns structured text in Uzbek.
    """
    _increment_ai_stat("vision")
    if not GEMINI_API_KEY:
        return None

    import PIL.Image
    import io

    try:
        image = PIL.Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"DEBUG: Image open error: {e}")
        return None

    models_to_try = [os.getenv("GEMINI_MODEL", "gemini-1.5-flash")]
    
    prompt = """
    You are an AI NUTRITIONIST with access to a vast database of food products.
    The photo shows a meal, drink, or packaged product.

    YOUR GOAL: Provide 99% ACCURATE nutrition data.

    STRICT ANALYSIS PROTOCOL:
    1. 🔍 SCAN TEXT: First, read ANY text on the package (Brand, Name, "0.5L", "100g", "Sugar Free").
    2. 🏭 IDENTIFY PRODUCT: If it's a known brand (Coca-Cola, Snickers, Lays, Nestlé, etc.), verify the exact product variant.
    3. 📏 PRECISE VOLUME/WEIGHT: 
       - If you see "0.5L", use exactly 500ml.
       - If it's a standard can, use 330ml.
       - If it's a standard bottle, use 500ml, 1L, or 1.5L based on visual size.
       - DO NOT GUESS if written on the label. USE THE LABEL DATA.
    4. 📚 OFFICIAL DATA: Use the official nutrition facts for that specific product (e.g. Coca-Cola Classic = 42kcal/100ml).
    5. 🧮 CALCULATION:
       - Example: Coca-Cola 0.5L -> 500ml * 0.42 = 210 kcal. (Show this math mentally and output final result).

    OUTPUT FORMAT:
    """
    
    if lang == 'ru':
        prompt += """
    🍽 <b>Анализ Калорий</b>

    🥘 <b>Продукт:</b> [Точный Бренд и Название]
    📏 <b>Объем/Вес:</b> [Точное измерение, напр. 0.5 Л]

    🔥 <b>Всего:</b> [Точный расчет] ккал

    📊 <b>БЖУ (на порцию, не на 100г):</b>
    🥩 Белки: ... г
    🥑 Жиры: ... г
    🍞 Углеводы: ... г

    <i>Рассчитано на основе данных упаковки и стандартов.</i> ✅
    Respond strictly in RUSSIAN.
    """
    else:
        prompt += """
    🍽 <b>Kaloriya Tahlili</b>

    🥘 <b>Mahsulot:</b> [Aniq Brend va Nomi]
    📏 <b>Hajmi:</b> [Aniq o'lchov, masalan 0.5 L]

    🔥 <b>Jami:</b> [Aniq hisob] kkal

    📊 <b>BJU (100g da emas, butun porsiyada):</b>
    🥩 Oqsil: ... g
    🥑 Yog‘: ... g
    🍞 Uglevod: ... g

    <i>Qadoqdagi ma'lumotlar va standartlarga asoslanib hisoblandi.</i> ✅
    Respond strictly in UZBEK.
    """

    global client
    if not GEMINI_API_KEY:
        return None
    
    if not client:
        try:
             client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
             print(f"DEBUG: Client Init Error: {e}")
             return None

    import PIL.Image
    import io

    try:
        image = PIL.Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"DEBUG: Image open error: {e}")
        return None

    prompt_text = prompt  # The prompt constructed above

    for model_name in MODELS_TO_TRY:
        try:
             print(f"DEBUG: Vision Attempt with {model_name}")
             response = client.models.generate_content(
                model=model_name,
                contents=[prompt_text, image],
                config=types.GenerateContentConfig(
                    safety_settings=SAFETY_SETTINGS,
                    temperature=0.4
                )
             )
             if response.text:
                import re
                text = response.text
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text.strip()
        except Exception as e:
            print(f"DEBUG: Vision failed with {model_name}: {e}")
            
    return None

def analyze_food_text(text, lang="uz", user_id=None):
    """
    Analyzes food text description using Gemini.
    Returns structured text in Uzbek.
    """
    _increment_ai_stat("vision")

    # 1. IMMEDIATE DB LOOKUP (Priority 1)
    # Check if the entire text matches a local dish
    from core.nutrition import lookup_usda_macros, format_nutrition_result
    # Simple normalization: lowercase and strip
    norm_text = text.lower().strip()
    db_match = lookup_usda_macros(norm_text, norm_text, user_id=user_id)
    if db_match and db_match.get("source") == "LOCAL":
        # Wrap it in the same structure as analyze_ingredients_list
        res = {
            "total_kcal": db_match["kcal_100g"],
            "total_protein": db_match["protein_100g"],
            "total_fat": db_match["fat_100g"],
            "total_carbs": db_match["carbs_100g"],
            "items": [{
                "name": norm_text,
                "kcal": db_match["kcal_100g"],
                "source": "LOCAL",
                "match_source": "DISH"
            }],
            "match_count": 1,
            "source_dist": {"LOCAL": 1, "USDA": 0, "AI": 0},
            "match_sources": {"DISH": 1, "ALIAS": 0, "FUZZY": 0, "FALLBACK": 0}
        }
        return format_nutrition_result(res, lang)

    global client
    if not GEMINI_API_KEY:
        return None

    if not client:
        try:
             client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
             print(f"DEBUG: Client Init Error: {e}")
             return None

    if lang == 'ru':
        prompt = f"""
        Пользователь съел: "{text}"
        
        Задача:
        1. Разбей еду на ингредиенты с указанием примерного веса/количества.
        2. Верни массив JSON с этими ингредиентами.
        
        Формат ответа:
        {{
          "items": ["продукты (вес/кол-во)", ...],
          "ai_estimate": {{
             "kcal": 250,
             "protein": 10,
             "fat": 5,
             "carbs": 30
          }}
        }}
        """
    else:
        prompt = f"""
        Foydalanuvchi yedi: "{text}"
        
        Vazifa:
        1. Ovqatni tarkibiy qismlarga ajrating (nomi va taxminiy vazni/soni).
        2. JSON formatida ingredientlar ro'yxatini qaytaring.
        
        Javob formati:
        {{
          "items": ["mahsulot nomi (vazni/soni)", ...],
          "ai_estimate": {{
             "kcal": 250,
             "protein": 10,
             "fat": 5,
             "carbs": 30
          }}
        }}
        """
        
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    safety_settings=SAFETY_SETTINGS,
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                import json
                from core.nutrition import analyze_ingredients_list, format_nutrition_result
                
                try:
                    data = json.loads(response.text)
                    items = data.get("items", [])
                    
                    # Try USDA Enrichment
                    usda_res = analyze_ingredients_list(items, user_id=user_id)
                    
                    if usda_res["match_count"] > 0:
                        # Success, use USDA data
                        return format_nutrition_result(usda_res, lang)
                    else:
                        # Fallback to AI estimate if no USDA matches
                        est = data.get("ai_estimate", {})
                        if lang == 'ru':
                            return f"🍽 <b>Анализ Калорий (AI)</b>\n\n🥘 <b>Еда:</b> {text}\n🔥 <b>Всего:</b> {est.get('kcal')} ккал\n📊 <b>БЖУ:</b> {est.get('protein')}г / {est.get('fat')}г / {est.get('carbs')}г\n\n<i>Приблизительный расчет AI.</i> ✅"
                        else:
                            return f"🍽 <b>Kaloriya Tahlili (AI)</b>\n\n🥘 <b>Ovqat:</b> {text}\n🔥 <b>Jami:</b> {est.get('kcal')} kkal\n📊 <b>BJU:</b> {est.get('protein')}g / {est.get('fat')}g / {est.get('carbs')}g\n\n<i>AI tomonidan taxminiy hisoblandi.</i> ✅"
                            
                except Exception as parse_err:
                    print(f"JSON Parse Error in analyze_food_text: {parse_err}")
                    continue

        except Exception as e:
            if "deadline" in str(e).lower() or "timeout" in str(e).lower():
                continue
            print(f"Gemini Text Error ({model_name}): {e}")
            
    return None

def ai_generate_fridge_recipe(user_profile, available_ingredients):
    """
    Generates 1-2 simple recipes based on available ingredients.
    Output is plain text (not JSON) for speed and flexibility.
    """
    _increment_ai_stat("meal")
    
    prompt = f"""
Siz professional oshpazsiz.
Foydalanuvchi maqsadi: {user_profile.get('goal')}
Bor mahsulotlar: {available_ingredients}

VAZIFA:
Shu mahsulotlardan 1 ta eng zo'r va tez pishadigan retsept yozing.
Javob FAQAT o'zbek tilida (lotin alifbosida) bo'lsin.

QAT'IY QOIDALAR:
1. ⚠️ JUDA QISQA BO'LSIN (Maksimal 200 belgi).
2. 🚫 Uydan yo'q narsa qo'shmang (faqat tuz/yog'/suv mumkin).
3. 📝 Format: 
   "🍳 [Nom]"
   "🥣 [Masalliqlar]"
   "👨‍🍳 [1 gap bilan tayyorlash]"
   
NAMUNA:
🍳 Pomidorli Tuxum
🥣 2 tuxum, 1 pomidor, tuz
👨‍🍳 Pomidorni to'g'rab qovuring, ustiga tuxumni chaqib, tuz sepib 5 daqiqa pishiring. Yoqimli ishtaha!
"""
    return call_gemini(prompt)

def format_gemini_text(raw_text, title):
    """Cleans and formats AI output."""
    if not raw_text:
        return ""
    
    import html
    import re
    
    # 1. Escape HTML special characters first (safe from random < or >)
    # quote=False ensures ' and " are not escaped, preventing &x27; issues
    text = html.escape(raw_text, quote=False)
    
    # 2. Convert Markdown bold (**text**) to HTML (<b>text</b>)
    # This regex finds **text** and replaces it with <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 3. Clean up any remaining Markdown artifacts if needed
    text = text.replace("##", "").replace("#", "")
    
    return f"<b>{title}</b>\n\n{text}"

def ai_provide_psychological_support(reason, lang="uz"):
    """Provides psychological support based on user's mood reason."""
    _increment_ai_stat("support")
    prompt = f"""
    Foydalanuvchi kayfiyati yomonligini aytdi. Sababi: "{reason}"
    
    Vazifa:
    - Unga qisqa, dalda beruvchi va psixologik yordam beruvchi xabar yoz.
    - Agar muammo jiddiy bo'lsa, oddiy maslahat ber (nafas olish mashqi, sayr qilish, va h.k.).
    - Do'stona va samimiy ohangda bo'lsin.
    - Maksimal 500 belgi.
    """
    
    if lang == 'ru':
        prompt += "\n     - Respond strictly in RUSSIAN.\n"
    else:
        prompt += "\n     - FAQAT O'zbek tilida (lotin alifbosida).\n"
    
    prompt += """
    Javob formati:
    [Matn]
    """
    
    response_text = call_gemini(prompt)
    if response_text:
        return response_text
    return "Tushunaman, ba'zida shunday kunlar bo'ladi. O'zingizni ehtiyot qiling va chuqur nafas oling. 💚"

def ai_generate_weekly_workout_json(user_profile, lang="uz", duration_weeks=1):
    """
    Generates a Weekly Workout Plan in strict JSON format.
    Supports duration_weeks > 1 by replicating the 1-week base plan.
    """
    user_id = user_profile.get('telegram_id')
    
    # Try DB Selection first (Priority)
    start_time = time.time()
    source = "AI"
    is_fallback = False
    fallback_reason = None
    
    if is_flag_enabled("db_workout_assembly", user_id):
        try:
            from core.workout_selector import select_workout_plan
            db_plan = select_workout_plan(user_profile)
            if db_plan:
                source = "DB"
                # Add motivation via AI (RESTRICTED)
                plan_summary = f"{user_profile.get('goal')} - {len(db_plan['schedule'])} kunlik reja"
                motivation, usage = generate_workout_motivation_uz(user_profile, plan_summary)
                
                # Log Workout Generation Event (LOCAL path)
                latency_ms = (time.time() - start_time) * 1000
                db.log_admin_event(
                    event_type="WORKOUT_GENERATION",
                    user_id=user_id,
                    success=True,
                    latency_ms=latency_ms,
                    meta={
                        "source": source,
                        "is_fallback": is_fallback,
                        "fallback_reason": fallback_reason,
                        "goal_tag": user_profile.get('goal'),
                        "level": user_profile.get('activity_level'),
                        "place": user_profile.get('place', 'uy'),
                        "ai_input_tokens": usage.get("input", 0),
                        "ai_output_tokens": usage.get("output", 0),
                        "ai_total_tokens": usage.get("input", 0) + usage.get("output", 0),
                        "ai_cost_usd": usage.get("cost", 0)
                    }
                )
                result = {"schedule": db_plan['schedule'], "motivation": motivation}
                
                # [PHASE 7.1] Explain Engine Propagation
                if db_plan.get("explanation"):
                    result["explanation"] = db_plan["explanation"]
                    
                # Replicate if needed
                if duration_weeks > 1:
                     original_schedule = list(result['schedule'])
                     for w in range(1, duration_weeks):
                         for day_item in original_schedule:
                             new_day = day_item.copy()
                             new_day['day'] = day_item['day'] + (7 * w)
                             result['schedule'].append(new_day)
                    
                return result
            else:
                is_fallback = True
                fallback_reason = "db_selector_returned_none"
        except Exception as e:
            logger.error(f"DB_WORKOUT_ASSEMBLY_FAILED: {e}")
            is_fallback = True
            fallback_reason = str(e)
            # Continues to AI fallback

    _increment_ai_stat("workout")
    
    # 0. CACHE CHECK
    
    # Workout depends on same factors
    profile_key = get_profile_key(user_profile)
    cached = db.get_workout_template(profile_key)
    
    if cached:
        print(f"DEBUG: Cache Hit for Workout: {profile_key}")
        try:
             # Log Event even for Cache Hit
             latency_ms = (time.time() - start_time) * 1000
             db.log_admin_event(
                 event_type="WORKOUT_GENERATION",
                 user_id=user_id,
                 success=True,
                 latency_ms=latency_ms,
                 meta={
                     "source": "CACHE",
                     "is_fallback": is_fallback,
                     "fallback_reason": fallback_reason,
                     "goal_tag": user_profile.get('goal'),
                     "level": user_profile.get('activity_level'),
                     "place": user_profile.get('place', 'uy'),
                     "ai_input_tokens": 0,
                     "ai_output_tokens": 0,
                     "ai_total_tokens": 0,
                     "ai_cost_usd": 0
                 }
             )
             plan_schedule = json.loads(cached['workout_json'])
             
             # Replicate if needed
             if duration_weeks > 1:
                  original_schedule = list(plan_schedule)
                  for w in range(1, duration_weeks):
                      for day_item in original_schedule:
                          new_day = day_item.copy()
                          new_day['day'] = day_item['day'] + (7 * w)
                          plan_schedule.append(new_day)

             return plan_schedule
        except Exception as e:
             print(f"Cache Corrupt: {e}")
    
    goal = user_profile.get('goal', 'Sog‘liq')
    
    # 1. System Prompt (JSON enforcer)
    from core.exercises import get_exercises_string
    
    # 1. System Prompt (JSON enforcer)
    # 1. System Prompt (JSON enforcer)
    # 1. System Prompt (JSON enforcer)
# language context
    lang_instruction = "FAQAT O‘ZBEK TILI (LOTIN ALIFBOSIDA)."
    if lang == "ru":
        lang_instruction = "FAQAT RUS TILI (CYRILLIC). Respond strictly in Russian."

    today_plan_template = "🏋️ Bugungi mashq rejasi"
    if lang == "ru":
        today_plan_template = "🏋️ План тренировки на сегодня"

    system_prompt = f"""
ROLE:
You are a professional fitness coach system for a Telegram bot.
Your task is to generate REALISTIC, SAFE, EFFECTIVE workout plans using ONLY the exercises provided below.

{get_exercises_string()}

IMPORTANT: {lang_instruction}

IMPORTANT RULES:
1. USE ONLY EXERCISES FROM THE LIST ABOVE. DO NOT INVENT EXERCISES.
2. If the user goal is weight loss, focus on high reps and cardio-style intervals.
3. If the user goal is muscle gain, focus on hypertrophy ranges (8-12 reps).

❌ You MUST NOT invent new exercises
❌ You MUST NOT change exercise names
❌ You MUST NOT remove Instagram links
❌ You MUST NOT generate workouts every single day

⸻

🧠 CORE RULES (VERY IMPORTANT)
	1.	ONLY use the exercise list provided below
	2.	Workout plans must include:
	•	Rest days
	•	Warm-up section
	•	Clear sets, reps, rest
	3.	No consecutive training of the same muscle group
	4.	Beginner-friendly, realistic recovery
	5.	Output must be CLEAR, HUMAN-READABLE, Telegram-ready

⸻

🗓 WORKOUT STRUCTURE RULES

Weekly logic:
	•	3–4 workout days per week
	•	1–2 rest days
	•	Muscle split logic:
	•	Upper Body -> Yuqori Tana (Ru: Верх тела)
	•	Lower Body -> Pastki Tana (Ru: Низ тела)
	•	Core / Full Body -> Butun Tana (Ru: Всё тело)
	•	Never train same muscle groups on consecutive days

⸻

📦 EXERCISE DATABASE (ONLY SOURCE)

{get_exercises_string()}

⸻

🏋️ DAY OUTPUT FORMAT (The 'exercises' field in JSON)

For workout days, the 'exercises' string MUST look exactly like this (use HTML bold tags <b>):

{today_plan_template} ({{Target Body Part Localized}})

⏱ Umumiy vaqt: 30–40 daqiqa (Ru: Общее время: 30-40 мин)
🎯 Maqsad: {{Vazn yo'qotish / Mushak o'stirish}} (Localized)

🔹 <b>Razminka (5 daqiqa)</b> (Ru: Разминка (5 мин))
- Yengil cho‘zilish
- Bo‘g‘imlarni aylantirish
- Yengil harakatlar

💪 <b>Asosiy mashqlar</b> (Ru: Основные упражнения)

1️⃣ <b>Exercise Name</b>
📌 Mushaklar: (Localized)
🔁 3 set × 12 marta (Ru: 3 подхода x 12 раз)
⏸ Dam: 60 soniya (Ru: Отдых 60 сек)
🎥 Link: <a href="Instagram URL">Video</a>

2️⃣ <b>Next Exercise Name</b>
... (Repeat for 4-5 exercises) ...

🧘 <b>Sovitish</b> (Ru: Заминка)
- Mushaklarni cho'zish

❌ DO NOT ADD SEPARATOR LINES LIKE "_______________________" AT THE END.

---

For REST DAYS, the 'exercises' field MUST be exactly:
"🧘‍♂️ <b>Bugun dam olish kuni</b>\\n\\nBugun tanani tiklaymiz.\\nYengil yurish yoki cho‘zilish tavsiya etiladi.\\n\\n👉 Ertaga mashq rejalashtirilgan"
(If Russian: "🧘‍♂️ <b>Сегодня День Отдыха</b>\\n\\nВосстанавливаем силы.\\nРекомендуется легкая прогулка.\\n\\n👉 Завтра тренировка")

⸻

OUTPUT FORMAT: JSON ONLY

{{
  "schedule": [
    {{
      "day": 1,
      "focus": "Yuqori Tana",
      "exercises": "...formatted string as above..."
    }},
    ... (for 7 days)
  ]
}}
"""

    # 2. User Prompt (Context)
    user_prompt = f"""
Foydalanuvchi ma'lumotlari:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Maqsad: {goal}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik: {user_profile.get('activity_level', 'O’rtacha')}

Talablar:
- 7 kunlik reja (JSON array "schedule" ichida). 
- DIQQAT: "schedule" array ichida roppa-rosa 7 ta element bo'lishi SHART.
- Dam olish kunlarini ham kiriting (masalan, 4-kun: Dam olish va tiklanish).
- JSON valid bo'lsin.
"""

    # ... (Prompt setup)

    # 3. Call AI
    try:
        response_text, usage_ai = ask_gemini(system_prompt, user_prompt, return_usage=True, user_id=user_id, feature="workout")
        # Clean markdown
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response_text)
        
        # Validate structure
        if "schedule" not in data or not isinstance(data["schedule"], list):
            raise Exception("Invalid JSON structure: missing 'schedule' list")
            
        if len(data["schedule"]) < 7:
             print("DEBUG: AI generated less than 7 days. Accepting partial but logging warning.")

        # VALIDATE CONTENT
        import re
        for day in data["schedule"]:
            if "exercises" not in day or not day.get("exercises"):
                day["exercises"] = "<i>Dam olish yoki yengil mashqlar</i>"
            else:
                # 1. Force spacing between numbered items (e.g. "1. Exercise" -> "\n\n1. Exercise")
                # Look for digit+dot at start of line OR preceded by newline/space
                clean_ex = day["exercises"]
                if "1." in clean_ex and "2." in clean_ex:
                     # Regex: find (digit dot) and ensure it has \n\n before it (unless it's the very start)
                     # Using a simple approach: Replace all "<br>" with "\n", then "\n" with "\n\n"
                     # But safer to just target the numbers.
                     
                     # First, clean existing newlines
                     clean_ex = clean_ex.replace("<br>", "\n").replace("\\n", "\n")
                     
                     # Replace any sequence of newlines before a number with exactly \n\n
                     clean_ex = re.sub(r'\s*(\d+\.)', r'\n\n\1', clean_ex)
                     
                     # Remove leading \n\n if added to the first item
                     clean_ex = clean_ex.lstrip()
                     
                     day["exercises"] = clean_ex
            
            # Fix 'focus' having weird suffixes if any
            if "focus" in day:
                day["focus"] = day["focus"].replace(" tuzat", "").replace(" mashqlari", "")
             
        # SAVE TO CACHE
        try:
             # data["schedule"] is the list we want to cache, or the whole data?
             # get_workout_template returns loaded json of cached['workout_json']
             # create_workout_template takes json string.
             # In cache check, we return json.loads(cached['workout_json']).
             # So we should save json.dumps(data["schedule"]).
             # Verify data["schedule"] is what we want. Yes.
             db.create_workout_template(profile_key, json.dumps(data["schedule"]))
        except Exception as e:
             # handle unique constraint or race conditions
             print(f"Workout Cache Save Warning: {e}")
             
        # Log Workout Generation Event (AI path or Fallback)
        latency_ms = (time.time() - start_time) * 1000
        db.log_admin_event(
            event_type="WORKOUT_GENERATION",
            user_id=user_id,
            success=True,
            latency_ms=latency_ms,
            meta={
                "source": "AI",
                "is_fallback": is_fallback,
                "fallback_reason": fallback_reason,
                "goal_tag": goal,
                "level": user_profile.get('activity_level'),
                "place": user_profile.get('place', 'uy'),
                "ai_input_tokens": usage_ai.get("input", 0),
                "ai_output_tokens": usage_ai.get("output", 0),
                "ai_total_tokens": usage_ai.get("input", 0) + usage_ai.get("output", 0),
                "ai_cost_usd": usage_ai.get("cost", 0)
            }
        )
        
        # Replicate if needed (After DB save, so DB has clean 1-week)
        if duration_weeks > 1:
             original_schedule = list(data['schedule'])
             for w in range(1, duration_weeks):
                 for day_item in original_schedule:
                     new_day = day_item.copy()
                     new_day['day'] = day_item['day'] + (7 * w)
                     bucket_day = new_day.get('day', 0)
                     # Optional: Should we update 'today_plan_template' or day names?
                     # Day names are usually static or managed by UI. 
                     # The AI output might hardcode "Dushanba" in formatted string. 
                     # We accept that repetition.
                     data['schedule'].append(new_day)

        return data

    except Exception as e:
        print(f"Error generating weekly workout JSON: {e}")
        return None

# -------------------------------------------------------------------------
# NEW: Single Meal Generation (VIP Swap)
# -------------------------------------------------------------------------
def ai_generate_single_meal(user_profile, meal_type, day_name="Bugun", lang="uz"):
    """Generates a SINGLE meal object for VIP swap."""
    
    # 1. Prompt
    lang_instruction = "Javob FAQAT O'zbek tilida (lotin alifbosida) bo'lsin."
    if lang == 'ru':
        lang_instruction = "Respond strictly in RUSSIAN."

    prompt = f"""
    Siz professional dietologsiz.
    Vazifa: "{day_name}" uchun yangi "{meal_type.upper()}" (Taom) o'ylab toping.
    {lang_instruction}
    
    Foydalanuvchi:
    - Maqsad: {user_profile.get('goal', 'Sog‘liq')}
    - Allergiya: {user_profile.get('allergies', 'Yo‘q')}
    
    TALABLAR:
    - 1 ta ovqat varianti.
    - JSON formatda.
    - Kaloriya: 300-600 kkal oralig'ida bo'lsin.
    
    JSON SCHEMA:
    {{
        "title": "Taom nomi",
        "kcal": 450,
        "ingredients": ["..."],
    """
    
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "kcal": {"type": "integer"},
            "ingredients": {"type": "array", "items": {"type": "string"}},
            "recipe": {"type": "string"},
            "steps": {"type": "array", "items": {"type": "string"}},
            "time_minutes": {"type": "integer"},
            "cost_level": {"type": "string"},
            "place": {"type": "string"}
        },
        "required": ["title", "kcal", "ingredients", "recipe", "steps"]
    }
    
    try:
         response_text = ask_gemini(
            "",  # No system prompt needed for this simple task
            prompt,
            response_mime_type="application/json",
            response_schema=schema,
            user_id=user_profile.get('telegram_id'),
            feature="meal_swap_vip"
         )

         import json
         return json.loads(response_text)
         
    except Exception as e:
        print(f"Single Meal Gen Error: {e}")
        return None

# -------------------------------------------------------------------------
# NEW: Free Tier Static Templates (Zero AI)
# -------------------------------------------------------------------------

def get_free_workout_template(user_profile, lang="uz"):
    """Returns a STATIC workout plan based on goal. No AI cost."""
    goal = user_profile.get('goal', 'Sog‘liq')
    is_weight_loss = "Ozish" in goal or "weight_loss" in goal or "Vazn tashlash" in goal
    
    # Localized text vars
    if lang == 'ru':
        t_focus = "Фокус"
        t_rest = "Отдых"
        t_week_end = "Конец недели"
        t_prep = "Подготовка к новой неделе"
        t_rest_desc_1 = "Сегодня день полного восстановления. Пейте больше воды."
        t_rest_desc_2 = "Погуляйте и отдохните."
        t_rest_desc_3 = "Для роста мышц нужен отдых."
        t_rest_desc_4 = "День восстановления."
        t_upper = "Верх тела"
        t_lower = "Низ тела"
        t_core = "Кор + Кардио"
        t_chest = "Грудь + Руки"
        t_shoulder = "Плечи + Кор"
    else:
        t_focus = "Focus"
        t_rest = "Dam olish (Rest)"
        t_week_end = "Haftalik yakun."
        t_prep = "Yangi haftaga tayyorgarlik."
        t_rest_desc_1 = "Bugun to'liq tiklanish kuni. Ko'proq suv iching."
        t_rest_desc_2 = "Sayr qiling va dam oling."
        t_rest_desc_3 = "Mushaklar o'sishi uchun dam kerak."
        t_rest_desc_4 = "Tiklanish kuni."
        t_upper = "Yuqori tana"
        t_lower = "Pastki tana"
        t_core = "Core + Kardio"
        t_chest = "Ko‘krak + Qo‘l"
        t_shoulder = "Yelka + Core"

    # Template 1: Weight Loss (Uy sharoiti)
    if is_weight_loss:
        return {
            "schedule": [
                {
                    "day": 1,
                    "focus": t_lower,
                    "exercises": "1. Squat — 3×12\n2. O‘tirib turish (Chair squat) — 3×15\n3. Oyoq ko‘tarish (Leg raise) — 3×10\n4. Yengil cho‘zilish — 5 daqiqa"
                },
                {
                    "day": 2,
                    "focus": t_rest, 
                    "exercises": t_rest_desc_1
                },
                {
                    "day": 3,
                    "focus": t_upper,
                    "exercises": "1. Knee push-up — 3×10\n2. Devorga suyangan push-up — 3×12\n3. Yelka aylantirish — 3×15\n4. Cho‘zilish — 5 daqiqa"
                },
                {
                    "day": 4,
                    "focus": t_rest,
                    "exercises": t_rest_desc_2
                },
                {
                    "day": 5,
                    "focus": t_core,
                    "exercises": "1. Plank — 3×20 soniya\n2. Crunch — 3×12\n3. Joyida yurish — 5 daqiqa\n4. Nafas mashqlari — 3 daqiqa"
                },
                {
                    "day": 6,
                    "focus": t_rest,
                    "exercises": t_week_end
                },
                {
                    "day": 7,
                    "focus": t_rest,
                    "exercises": t_prep
                }
            ]
        }
    
    # Template 2: Muscle Gain / General (Zal/Uy)
    return {
        "schedule": [
            {
                "day": 1,
                "focus": t_chest,
                "exercises": "1. Push-up — 4×10\n2. Dumbbell curl — 3×12\n3. Triceps dip — 3×10"
            },
            {
                "day": 2,
                "focus": t_rest,
                "exercises": t_rest_desc_3
            },
            {
                "day": 3,
                "focus": "Oyoq" if lang != 'ru' else "Ноги",
                "exercises": "1. Squat — 4×12\n2. Lunge — 3×10\n3. Calf raise — 3×15"
            },
            {
                "day": 4,
                "focus": t_rest,
                "exercises": t_rest_desc_4
            },
            {
                "day": 5,
                "focus": t_shoulder,
                "exercises": "1. Shoulder press — 3×10\n2. Plank — 3×30 soniya"
            },
            {
                "day": 6,
                "focus": t_rest,
                "exercises": "Dam olish." if lang != 'ru' else "Отдых."
            },
            {
                "day": 7,
                "focus": t_rest,
                "exercises": "Tayyorgarlik." if lang != 'ru' else "Подготовка."
            }
        ]
    }

def get_free_menu_template(lang="uz"):
    """Returns a STATIC 1-day menu template. Zero AI cost."""
    # This is a 1-day template replicated for structure compliance
    # But for Free users, we only show "Bugungi Menyu".
    
    if lang == 'ru':
        day_name = "Сегодня"
        advice = "Вы на верном пути 🔥."
        t_egg = "Яйца и овощи"
        i_egg = ["Яйца (2 шт)", "Помидор (1)", "Огурец (1)"]
        s_egg = ["Сварить яйца", "Нарезать овощи"]
        t_snack_title = "Яблоко"
        i_apple = ["Яблоко (1 шт)"]
        s_snack = ["Помыть и съесть"]
        t_soup = "Куриный суп"
        i_soup = ["Курица (150г)", "Картофель (1)", "Морковь (1)"]
        s_soup = ["Сварить мясо", "Добавить овощи"]
        t_dinner = "Гречка + салат"
        i_dinner = ["Гречка (80г)", "Капуста (100г)"]
        s_dinner = ["Гречку запарить", "Нарезать салат"]
        cost = "Эконом"
        place = "Дом"
        
        l_title = "🔒 Только Premium"
        l_steps = "Меню в YASHA Plus"
        l_status = "День X (Premium)"
        l_advice = "Полное меню только в YASHA Plus."
    else:
        day_name = "Bugun"
        advice = "Siz yaxshi ketayapsiz 🔥. Natija davomiylikda."
        t_egg = "Tuxum va sabzavot"
        i_egg = ["Tuxum (2 dona)", "Pomidor (1 dona)", "Bodring (1 dona)"]
        s_egg = ["Tuxumni qaynating", "Sabzavotlarni to'g'rang"]
        t_snack_title = "Olma"
        i_apple = ["Olma (1 dona)"]
        s_snack = ["Yuvib iste'mol qiling"]
        t_soup = "Tovuq sho‘rvasi"
        i_soup = ["Tovuq (150g)", "Kartoshka (1)", "Sabzi (1)"]
        s_soup = ["Go'shtni qaynatib oling", "Sabzavot soling"]
        t_dinner = "Grechka + salat"
        i_dinner = ["Grechka (80g)", "Karam (100g)"]
        s_dinner = ["Grechkani dimlang", "Salat to'g'rang"]
        cost = "Arzon"
        place = "uy"
        
        l_title = "🔒 Faqat Premiumda"
        l_steps = "YASHA Plus taomnomasi"
        l_status = "Kun {i} (Premium)"
        l_advice = "To'liq menyu faqat YASHA Plus'da."

    daily_plan = {
        "day": 1,
        "day_name": day_name,
        "total_kcal": 1400,
        "micro_advice": advice,
        "breakfast": {
            "title": t_egg,
            "kcal": 350,
            "items": i_egg,
            "steps": s_egg,
            "time_minutes": 10,
            "cost_level": cost,
            "place": place
        },
        "snack": {
            "title": t_snack_title,
            "kcal": 150,
            "items": i_apple, 
            "steps": s_snack
        },
        "lunch": {
            "title": t_soup,
            "kcal": 500,
            "items": i_soup,
            "steps": s_soup,
            "time_minutes": 45,
            "cost_level": cost,
            "place": place
        },
        "dinner": {
            "title": t_dinner,
            "kcal": 400,
            "items": i_dinner,
            "steps": s_dinner,
            "time_minutes": 25,
            "cost_level": cost,
            "place": place
        }
    }
    
    # Replicate for 7 days structure (so JSON parsing doesn't break)
    menu_list = []
    
    # Locked Meal Object
    locked_meal = {
         "title": l_title,
         "kcal": 0,
         "ingredients": ["..."],
         "preparation_steps": [l_steps],
         "time_minutes": 0,
         "cost_level": "-",
         "place": "-"
    }

    for i in range(1, 8):
        if i == 1:
            menu_list.append(daily_plan)
        else:
            day_copy = {
                "day": i,
                "day_name": l_status.replace("{i}", str(i)),
                "total_kcal": 0,
                "micro_advice": l_advice,
                "breakfast": locked_meal,
                "lunch": locked_meal,
                "dinner": locked_meal,
                "snack": locked_meal
            }
            menu_list.append(day_copy)
        
    return {
        "menu": menu_list,
        "shopping_list": {} # Empty for Free
    }

# -------------------------------------------------------------------------
# NEW: Fridge / Recipe Suggestion (Premium)
# -------------------------------------------------------------------------
def ai_suggest_recipe(user_profile, ingredients_text, lang="uz"):
    """Suggests a healthy recipe based on user ingredients."""
    
    prompt = f"""
    Siz professional dietologsiz.
    
    Foydalanuvchi maqsadi: {user_profile.get('goal', 'Sog‘liq')}
    Muzlatgichda bor mahsulotlar: "{ingredients_text}"
    
    VAZIFA:
    Shu mahsulotlardan (va qo'shimcha oddiy narsalardan) foydalanib, 
    bitta sog'lom va foydali retsept tuzing.
    
    Javob formati (FAQAT O'zbek tilida, lotin alifbosida):
    🍽 **Taom nomi**
    
    🛒 **Kerakli masalliqlar:**
    - ...
    
    👩‍🍳 **Tayyorlash:**
    1. ...
    2. ...
    
    💡 **Foydasi:** ...
    
    Qisqa, lo'nda va tushunarli bo'lsin.
    """
    
    if lang == 'ru':
        prompt = f"""
    You are a professional nutritionist.
    
    Goal: {user_profile.get('goal', 'Sog‘liq')}
    Ingredients in fridge: "{ingredients_text}"
    
    TASK:
    Create ONE healthy recipe using these ingredients.
    
    Format (Response strictly in RUSSIAN):
    🍽 **Название Блюда**
    
    🛒 **Ингредиенты:**
    - ...
    
    👩‍🍳 **Приготовление:**
    1. ...
    2. ...
    
    💡 **Польза:** ...
    
    Keep it short and clear.
    """
    
    try:
        response_text = ask_gemini("You are a professional nutritionist expert.", prompt)
        return response_text
    except Exception as e:
        print(f"Fridge Gen Error: {e}")
        return None

# -------------------------------------------------------------------------
# Free Tier Mood Support (Static)
# -------------------------------------------------------------------------
def get_free_mood_support_template(lang="uz"):
    """Returns a static supportive message for Free users."""
    import random
    
    if lang == 'ru':
        templates = [
            (
                "😔 **Понимаю, бывают такие дни.**\n\n"
                "Сейчас главное — уделить время себе. "
                "Сделайте глубокий вдох и выпейте стакан воды. "
                "Трудности временны, а вы сильны. 💚\n\n"
                "💡 _В YASHA Plus AI может проанализировать ваше состояние и дать "
                "персональные психологические советы._"
            ),
            (
                "🫂 **Вы не одни.**\n\n"
                "У каждого бывают трудные дни. "
                "Постарайтесь сегодня просто отдохнуть. "
                "Все будет хорошо ✨\n\n"
                "💡 _В YASHA Plus AI тренер может пообщаться с вами "
                "и помочь справиться со стрессом._"
            ),
            (
                "🌧 **После дождя всегда выходит солнце.**\n\n"
                "Настроение меняется, но цель остается. "
                "Берегите себя.\n\n"
            )
        ]
    else:
        templates = [
            (
                "😔 **Tushunaman, ba'zan shunday bo'ladi.**\n\n"
                "Hozir eng muhimi — o'zingizga vaqt ajratish. "
                "Chuqur nafas oling va bir stakan suv iching. "
                "Muammolar vaqtinchalik, siz esa kuchlisiz. 💚\n\n"
                "💡 _YASHA Plus'da AI sizning vaziyatingizni tahlil qilib, "
                "aniq psixologik maslahatlar bera oladi._"
            ),
            (
                "🫂 **Siz yolg'iz emassiz.**\n\n"
                "Har bir inson qiyin kunlarni boshdan kechiradi. "
                "Bugun shunchaki dam olishga harakat qiling. "
                "Hammasi yaxshi bo'ladi ✨\n\n"
                "💡 _YASHA Plus'da AI murabbiy siz bilan suhbatlashib, "
                "stressni yengishga yordam beradi._"
            ),
            (
                "🌧 **Yomg'irdan keyin albatta quyosh chiqadi.**\n\n"
                "Kayfiyat o'zgaruvchan, lekin maqsadingiz o'zgarmasin. "
                "O'zingizni ehtiyot qiling.\n\n"
                "💡 _YASHA Plus foydalanuvchilari uchun AI har qanday vaziyatda "
                "individual yechim taklif qiladi._"
            )
        ]
    return random.choice(templates)
