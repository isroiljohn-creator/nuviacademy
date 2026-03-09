import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Configurable model with fallback
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        try:
            model = genai.GenerativeModel(model_name)
        except:
             # Fallback if specific model fails (e.g. deprecation)
            print(f"Warning: Model {model_name} failed, falling back to gemini-1.5-flash")
            model = genai.GenerativeModel("gemini-1.5-flash")
            
        print(f"DEBUG: Gemini AI initialized successfully using {model_name}.")
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
else:
    print("DEBUG: GEMINI_API_KEY not found in environment variables.")

def get_offline_workout(user_profile):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
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

def get_offline_menu(user_profile):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
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
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Models to try in order
# Primary: from Env (default 2.5-flash)
# Fallback: 1.5-flash (more stable/faster/cheaper)
MODELS_TO_TRY = []
primary = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MODELS_TO_TRY.append(primary)
if primary != "gemini-1.5-flash":
    MODELS_TO_TRY.append("gemini-1.5-flash")

def get_profile_key(profile):
    """Generates a cache key for deduplication."""
    age = int(profile.get('age', 25))
    age_band = f"{age // 5 * 5}-{(age // 5 * 5) + 4}"
    
    return f"{profile.get('gender')}|{profile.get('goal')}|{profile.get('activity_level')}|{profile.get('allergies')}|{age_band}"

# Usage Stats
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

def ask_gemini(system_prompt, user_prompt):
    """
    Centralized helper to call Gemini with model fallback.
    Returns plain text response or raises Exception.
    """
    global model
    
    if not GEMINI_API_KEY:
        raise Exception("API Key not found")

    # Combine system and user prompt
    full_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
    
    last_error = None
    
    for model_name in MODELS_TO_TRY:
        try:
            # Configure and instantiate specific model
            genai.configure(api_key=GEMINI_API_KEY)
            current_model = genai.GenerativeModel(model_name)
            
            print(f"DEBUG: Attempting AI generation with model: {model_name}")
            
            response = current_model.generate_content(
                full_prompt, 
                safety_settings=SAFETY_SETTINGS,
                request_options={'timeout': 60}
            )
            
            if response.text:
                return response.text.strip()
            
        except Exception as e:
            print(f"DEBUG: Model {model_name} failed: {e}")
            try:
                if hasattr(response, 'prompt_feedback'):
                    print(f"DEBUG: Prompt Feedback: {response.prompt_feedback}")
            except:
                pass
            last_error = e
            continue # Try next model
            
    # If all models fail
    print("ERROR: All AI models failed.")
    AI_USAGE_STATS["errors"] += 1
    raise last_error or Exception("All AI models failed")

def call_gemini(prompt):
    """Legacy wrapper for backward compatibility, redirects to ask_gemini"""
    try:
        return ask_gemini("You are a helpful assistant.", prompt)
    except Exception as e:
        print(f"DEBUG: call_gemini caught exception: {e}")
        return None

def ai_generate_workout(user_profile):
    """Generates a weekly workout plan using Gemini or fallback."""
    AI_USAGE_STATS["workout"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    prompt = f"""
Siz Telegram uchun qisqa, silliq, tushunarli mashq rejalari tuzadigan professional fitness trenerisiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Maqsad: {user_profile.get('goal')}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik darajasi: {user_profile.get('activity_level', 'Belgilanmagan')}

🎯 Vazifa:
Foydalanuvchiga uy sharoitida bajariladigan 3 kunlik mashq rejasi tuzing.

📌 FORMAT TALABLARI:
- HTML ishlatma (<p>, <ul>, <li> yo‘q).
- Muhim joylarni ajratish uchun **yulduzcha** (markdown) ishlat.
- Emojilarni minimal ishlat (faqat bo‘lim sarlavhalarida).
- Har bir kun quyidagicha struktura bo‘lsin:

**1-kun: Ko‘krak & Triceps**  
- Mashq 1 — takrorlar  
- Mashq 2 — takrorlar  
- Mashq 3 — takrorlar  

**2-kun: Oyoq & Yelka**  
- ...

**3-kun: Orqa & Core**  
- ... 

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.
🧩 Har bir mashq sodda va uyda qilinadigan bo‘lsin.
🧩 Javob faqat matn ko‘rinishida bo‘lsin.
"""
    
    response_text = call_gemini(prompt)
    if response_text and len(response_text) > 50: # Ensure meaningful response
        return format_gemini_text(response_text, "🏋️‍♂️ Sizning Individual Mashq Rejangiz")
        
    print(f"DEBUG: AI failed or returned empty. Using fallback for user {user_profile.get('name')}")
    return get_offline_workout(user_profile)

def ai_generate_menu(user_profile):
    """Generates a weekly meal plan using Gemini or fallback."""
    AI_USAGE_STATS["meal"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    
    # Build allergy warning if present
    allergy_text = user_profile.get('allergies')
    allergy_section = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']:
        allergy_section = f"\n\n⚠️ ⚠️ ⚠️ JUDA MUHIM ⚠️ ⚠️ ⚠️\nFoydalanuvchida {allergy_text} ga ALLERGIYA BOR!\nTavsiya qilingan ovqatlarda BU MAHSULOTLAR BO'LMASLIGI KERAK!\nAlternativ mahsulotlar tavsiya qiling.\n"
    
    prompt = f"""
Siz Telegram uchun ovqatlanish bo'yicha qisqa, silliq, o'qilishi oson matn yozadigan dietologsiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Bo'y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik darajasi: {user_profile.get('activity_level', 'Belgilanmagan')}
Maqsad: {user_profile.get('goal')}{allergy_section}

🎯 Vazifa:
Foydalanuvchiga 3 kunlik ovqatlanish rejasi tuzing.

📌 MUHIM SHARTLAR:
1. O'zbekiston bozoriga mos mahsulotlar bo'lsin (avokado, qimmat baliqlar o'rniga — tuxum, tovuq, mol go'shti, mahalliy mevalar).
2. Xaridlar ro'yxatini YOZMANG (bu alohida so'raladi).
3. Agar foydalanuvchida allergiya yoki kasallik bo'lsa, menyuni shunga qarab qat'iy moslang!

📌 FORMAT TALABLARI:
- Hech qanday HTML (<p>, <br>, <ul>, <li>) ishlatma.
- Muhim joylarni ajratish uchun **yulduzcha** (markdown) ishlat.
- Emojilarni kam ishlat — faqat kun nomlarida yoki sarlavhalarda.
- Har kun quyidagicha bo'lsin:

**1-kun**
- Nonushta: ...
- Tushlik: ...
- Kechki: ...
- Snack: ...

- 3 kunda ham struktura bir xil bo'lsin.

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.

📢 Javob faqat matn ko'rinishida bo'lsin.
"""

    response_text = call_gemini(prompt)
    
    if response_text:
        print(f"DEBUG: AI Response Length: {len(response_text)}")
    else:
        print("DEBUG: AI Response was None or Empty.")

    if response_text and len(response_text) > 50:
        return format_gemini_text(response_text, "Sizning ovqatlanish rejangiz")

    print(f"DEBUG: AI failed validation (len > 50). Using fallback for user {user_profile.get('name')}")
    return get_offline_menu(user_profile)


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

def ai_generate_monthly_menu_json(user_profile):
    """Generates a 30-day structured meal plan + shopping list in JSON."""
    AI_USAGE_STATS["meal"] += 1
    AI_USAGE_STATS["total_requests"] += 1

    # 0. CACHE CHECK
    from core.db import db
    import json
    
    profile_key = get_profile_key(user_profile)
    cached = db.get_menu_template(profile_key)
    
    if cached:
        print(f"DEBUG: Cache Hit for Menu: {profile_key}")
        try:
             return {
                 "menu": json.loads(cached['menu_json']),
                 "shopping_list": json.loads(cached['shopping_list_json'])
             }
        except Exception as e:
             print(f"Cache Corrupt: {e}")

    allergy_text = user_profile.get('allergies')
    allergy_section = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']:
        allergy_section = f"DIQQAT: Foydalanuvchida {allergy_text} ga allergiya bor. Menyuda bular qat'iyan bo'lmasin!"

    
    
    
    # 1. System Prompt (Softened Role)
    system_prompt = """
Siz O'zbekistonda yashovchi foydali yordamchisiz.
Vazifangiz: 7 kunlik (HAFTALIK) VARIATIV va FOYDALI taomlar ro'yxatini tuzish.
Har bir kun har xil bo'lishi SHART.

Javob formati: FAQAT JSON.

QAT'IY QOIDALAR:
1. Tilda aralashma bo'lmasin. FAQAT O'ZBEK TILI. (Inglizcha so'z umuman ishlatilmasin: "Oatmeal" -> "Suli bo'tqasi", "Chicken" -> "Tovuq").
2. Mahsulotlar O'ZBEK BOZORIDA topiladigan bo'lsin.
3. Milliy taomlarni (yog'siz variantlarini) qo'shish tavsiya etiladi (Moshkichiri, Mastava, Shurva).
4. Taomlar takrorlanmasin (yoki kam takrorlansin).
"""

    # 2. User Prompt (Data)
    user_prompt = f"""
Ma'lumotlar:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Bo'y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik: {user_profile.get('activity_level', 'O’rtacha')}
Maqsad: {user_profile.get('goal')}
{allergy_section}

Talablar:
- 7 kunlik reja (JSON array "menu" ichida). 
- DIQQAT: "menu" array ichida roppa-rosa 7 ta element bo'lishi SHART. Kam bo'lmasin.
- Har bir kun uchun: day, breakfast, lunch, dinner, snack.
- O'zbek milliy va yevropa taomlarini aralashtirib yoz.
- "shopping_list" da FAQAT ENG ASOSIY 10-15 ta mahsulot bo'lsin.
  - Uyda bor narsalarni (tuz, yog', un, shakar) YOZMA.
  - Qimmat narsalarni YOZMA (Avokado, Losos, Kinoa kerak emas).
  - Oddiy, hamyonbop va bozorbop mahsulotlarni yoz (Tuxum, Tovuq, Sabzi, Kartoshka).
  - Ro'yxat "kunlarga bo'lingan" holda emas, umumiy bo'lsin, lekin ixcham.
- JSON valid bo'lsin.
"""

    
    # 3. Model Configuration
    # Using 'gemini-1.5-flash' as stable version
    model_name = 'gemini-2.5-flash'
    
    try:
        # print(f"DEBUG: Trying Menu Gen with {model_name}")
        
        genai.configure(api_key=GEMINI_API_KEY)
        curr_model = genai.GenerativeModel(model_name)
        
        full_text_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
        
        # Define Schema for Strict Output
        generation_config = {
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "menu": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "day": {"type": "integer"},
                                "breakfast": {"type": "string"},
                                "lunch": {"type": "string"},
                                "dinner": {"type": "string"},
                                "snack": {"type": "string"}
                            },
                            "required": ["day", "breakfast", "lunch", "dinner", "snack"]
                        }
                    },
                    "shopping_list": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["menu", "shopping_list"]
            }
        }

        try:
            response = curr_model.generate_content(
                full_text_prompt,
                safety_settings=SAFETY_SETTINGS,
                generation_config=generation_config,
                request_options={'timeout': 120} 
            )
        except Exception as api_error:
            # Catch API errors (429, 500, etc) and re-raise with clear message
            # print(f"DEBUG: API Error: {api_error}")
            if "429" in str(api_error) or "quota" in str(api_error).lower():
                 raise Exception("AI charchadi (Limit tugadi). Iltimos, 1-2 daqiqadan keyin urinib ko'ring.")
            raise Exception(f"Google API Error: {api_error}")

        response_text = response.text
        
        # Check for safety blocking if text is empty but candidate exists
        if not response_text:
            if hasattr(response, 'prompt_feedback'):
                 feedback = response.prompt_feedback
                 print(f"DEBUG: Safety Feedback: {feedback}")
                 raise Exception(f"Blocked by Safety Filters: {feedback}")
            raise Exception("Empty response text from AI (No reason given)")

        print(f"DEBUG: AI Output ({model_name}): {response_text[:200]}...")

        # Robust JSON extraction
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        clean_json = json_match.group(0) if json_match else response_text

        try:
            import json
            data = json.loads(clean_json)
            
            # ----------------------------------------------------------------
            # ROBUST CLEANING (Fix "tuzat" and other AI glitches)
            # ----------------------------------------------------------------
            if "menu" in data and isinstance(data["menu"], list):
                for day in data["menu"]:
                     for meal in ["breakfast", "lunch", "dinner", "snack"]:
                         if meal in day and isinstance(day[meal], str):
                             # Remove "tuzat" or similar command leaks
                             clean_text = day[meal].replace(" tuzat", "").replace(" yoz", "")
                             
                             # Ensure capitalization
                             if clean_text:
                                 clean_text = clean_text[0].upper() + clean_text[1:]
                                 
                             day[meal] = clean_text

            if "shopping_list" in data and isinstance(data["shopping_list"], list):
                new_list = []
                for item in data["shopping_list"]:
                    if isinstance(item, str):
                        clean_item = item.replace(" tuzat", "").strip()
                        if clean_item:
                             new_list.append(clean_item)
                data["shopping_list"] = new_list
            # ----------------------------------------------------------------

            # SAVE TO CACHE
            try:
                # Ensure it's valid data before saving
                if "menu" in data and "shopping_list" in data:
                     db.create_menu_template(
                         profile_key,
                         json.dumps(data["menu"]),
                         json.dumps(data["shopping_list"])
                     )
            except Exception as e:
                 print(f"Cache Save Error: {e}")

            return data
        except:
            import ast
            data = ast.literal_eval(clean_json)
            return data
    except Exception as e:
        print(f"DEBUG: Model {model_name} failed: {e}")
        # RE-RAISE THE EXACT ERROR so bot/workout.py displays it
        raise e
        


def ai_answer_question(question):
    """Answers a general fitness question using Gemini."""
    AI_USAGE_STATS["chat"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    response_text = call_gemini(f"Siz fitnes murabbiyisiz. Savolga qisqa va aniq javob bering (o'zbek tilida): {question}")
    if response_text:
        return format_gemini_text(response_text, "Savolingizga javob")
            
    return "⚠️ AI hozircha band. Iltimos, keyinroq urinib ko‘ring."

def ai_generate_shopping_list(user_profile):
    """Generates a shopping list based on user profile and health context."""
    AI_USAGE_STATS["shopping"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    
    # Build allergy/health warning
    allergy_text = user_profile.get('allergies')
    health_context = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']:
        health_context = f"\n⚠️ DIQQAT: Foydalanuvchida {allergy_text} ga allergiya bor. Ro'yxatga bularni qo'shmang!\n"
        
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
    
    response = call_gemini(prompt)
    if response:
        return format_gemini_text(response, "Xaridlar Ro'yxati")
    return None

def analyze_food_image(image_data):
    """
    Analyzes food image using Gemini Vision.
    Returns structured text in Uzbek.
    """
    AI_USAGE_STATS["vision"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    if not GEMINI_API_KEY:
        return None

    import PIL.Image
    import io

    try:
        image = PIL.Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"DEBUG: Image open error: {e}")
        return None

    models_to_try = ['gemini-2.5-flash']
    
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

    OUTPUT FORMAT (Uzbek):
    🍽 <b>Kaloriya Tahlili</b>

    🥘 <b>Mahsulot:</b> [Aniq Brend va Nomi]
    📏 <b>Hajmi:</b> [Aniq o'lchov, masalan 0.5 L]

    🔥 <b>Jami:</b> [Aniq hisob] kkal

    📊 <b>BJU (100g da emas, butun porsiyada):</b>
    🥩 Oqsil: ... g
    🥑 Yog‘: ... g
    🍞 Uglevod: ... g

    <i>Qadoqdagi ma'lumotlar va standartlarga asoslanib hisoblandi.</i> ✅
    """

    # Ensure config is set (idempotent if already set globally, but good to be sure)
    # genai.configure is global, so if it was called at startup, we are good.
    # But we might need to instantiate specific models.

    for model_name in models_to_try:
        try:
            # Reuse global config, just instantiate model
            vision_model = genai.GenerativeModel(model_name)
            
            response = vision_model.generate_content([prompt, image], safety_settings=SAFETY_SETTINGS)
            if response.text:
                # Force convert Markdown bold to HTML bold
                import re
                text = response.text
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
        except Exception as e:
            print(f"DEBUG: Vision failed with {model_name}: {e}")
            
    return None

def analyze_food_text(text):
    """
    Analyzes food text description using Gemini.
    Returns structured text in Uzbek.
    """
    AI_USAGE_STATS["vision"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    global model
    if not GEMINI_API_KEY:
        return None

    try:
        # Use global model if available and it supports text (2.5 flash does)
        if not model:
             model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        Foydalanuvchi yedi: "{text}"
        
        Vazifa:
        - Ovqat tarkibi va porsiyasini tahlil qiling.
        - Umumiy kaloriya va BJU (Oqsil, Yog', Uglevod) ni hisoblang.
        
        Javob formati (O'zbek tilida):
        🍽 <b>Kaloriya Tahlili</b>

        🥘 <b>Ovqat:</b> ...
        📏 <b>Porsiya:</b> ...

        🔥 <b>Jami:</b> ... kkal

        📊 <b>BJU:</b>
        🥩 Oqsil: ... g
        🥑 Yog‘: ... g
        🍞 Uglevod: ... g

        <i>Bu taxminiy hisob, lekin kunlik nazorat uchun yetarli.</i> ✅
        """
        
        try:
            # We must use 'generate_content' with 'generation_config' OR just pass timeout?
            # New SDK allows request_options={'timeout': 15}
            # Or generation_config ... let's try direct call arguments if supported, 
            # but standard is generation_config usually for params.
            # Timeout is likely request_option.
            
            # Since version 0.3.0+, we can use logic. 
            # Assuming standard google.generativeai setup.
            # We'll rely on our own Timer wrapping OR use library support.
            # simplest is to trust 'generation_config' or just catch generic socket timeouts.
            # Let's add request_options which is supported in newer SDKs.
            
            response = model.generate_content(
                prompt,
                safety_settings=SAFETY_SETTINGS,
                request_options={'timeout': 20} # 20 seconds strict timeout
            )
            
            if response.text:
                import re
                text = response.text
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
            return None
        except Exception as e:
            # Catch deadline exceeded or other network errors
            if "deadline" in str(e).lower() or "timeout" in str(e).lower():
                return "⚠️ Kechirasiz, AI javob berishga ulgurmadi. Iltimos, qaytadan urinib ko'ring."
            print(f"Gemini Text Error: {e}")
            return "⚠️ AI xizmatida vaqtincha uzilish bo'ldi. Keyinroq urinib ko'ring."
    except Exception as e:
        print(f"Gemini Text Error: {e}")
        return None

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

def ai_provide_psychological_support(reason):
    """Provides psychological support based on user's mood reason."""
    AI_USAGE_STATS["support"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    prompt = f"""
    Foydalanuvchi kayfiyati yomonligini aytdi. Sababi: "{reason}"
    
    Vazifa:
    - Unga qisqa, dalda beruvchi va psixologik yordam beruvchi xabar yoz.
    - Agar muammo jiddiy bo'lsa, oddiy maslahat ber (nafas olish mashqi, sayr qilish, va h.k.).
    - Do'stona va samimiy ohangda bo'lsin.
    - Maksimal 500 belgi.
    - O'zbek tilida.
    
    Javob formati:
    [Matn]
    """
    
    response_text = call_gemini(prompt)
    if response_text:
        return response_text
    return "Tushunaman, ba'zida shunday kunlar bo'ladi. O'zingizni ehtiyot qiling va chuqur nafas oling. 💚"

def ai_generate_weekly_workout_json(user_profile):
    """
    Generates a 7-DAY Weekly Workout Plan in strict JSON format.
    Mirrors the logic of the menu system.
    """
    AI_USAGE_STATS["workout"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    
    # 0. CACHE CHECK
    from core.db import db
    import json
    
    # Workout depends on same factors
    profile_key = get_profile_key(user_profile)
    cached = db.get_workout_template(profile_key)
    
    if cached:
        print(f"DEBUG: Cache Hit for Workout: {profile_key}")
        try:
             # Just return what we need. The caller likely expects the Raw JSON string or Dict?
             # ai_generate_weekly_workout_json usually returns Dict.
             return json.loads(cached['workout_json'])
        except Exception as e:
             print(f"Cache Corrupt: {e}")
    
    goal = user_profile.get('goal', 'Sog‘liq')
    
    # 1. System Prompt (JSON enforcer)
    from core.exercises import get_exercises_string
    
    # 1. System Prompt (JSON enforcer)
    # 1. System Prompt (JSON enforcer)
    # 1. System Prompt (JSON enforcer)
    system_prompt = f"""
ROLE:
You are a professional fitness coach system for a Telegram bot.
Your task is to generate REALISTIC, SAFE, EFFECTIVE workout plans using ONLY the exercises provided below.

{get_exercises_string()}

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
	•	Upper Body -> Yuqori Tana
	•	Lower Body -> Pastki Tana
	•	Core / Full Body -> Butun Tana
	•	Never train same muscle groups on consecutive days

⸻

📦 EXERCISE DATABASE (ONLY SOURCE)

{get_exercises_string()}

⸻

🏋️ DAY OUTPUT FORMAT (The 'exercises' field in JSON)

For workout days, the 'exercises' string MUST look exactly like this (use HTML bold tags <b>):

🏋️ Bugungi mashq rejasi ({{Yuqori Tana / Pastki Tana / Butun Tana}})

⏱ Umumiy vaqt: 30–40 daqiqa
🎯 Maqsad: {{Vazn yo'qotish / Mushak o'stirish}} (Uzbek)

🔹 <b>Razminka (5 daqiqa)</b>
- Yengil cho‘zilish
- Bo‘g‘imlarni aylantirish
- Yengil harakatlar

💪 <b>Asosiy mashqlar</b>

1️⃣ <b>Exercise Name</b>
📌 Mushaklar: (Uzbek)
🔁 3 set × 12 marta
⏸ Dam: 60 soniya
🎥 Link: <a href="Instagram URL">Video darslik</a>

2️⃣ <b>Next Exercise Name</b>
... (Repeat for 4-5 exercises) ...

🧘 <b>Sovitish</b>
- Mushaklarni cho'zish

❌ DO NOT ADD SEPARATOR LINES LIKE "_______________________" AT THE END.

---

For REST DAYS, the 'exercises' field MUST be exactly:
"🧘‍♂️ <b>Bugun dam olish kuni</b>\\n\\nBugun tanani tiklaymiz.\\nYengil yurish yoki cho‘zilish tavsiya etiladi.\\n\\n👉 Ertaga mashq rejalashtirilgan"

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
    import json
    try:
        response_text = ask_gemini(system_prompt, user_prompt)
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

        return data

    except Exception as e:
        print(f"Error generating weekly workout JSON: {e}")
        return None
