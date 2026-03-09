import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model_name = 'gemini-2.5-flash'
model = genai.GenerativeModel(model_name)

system_prompt = """
Siz O'zbekistonda yashovchi foydali yordamchisiz.
Vazifangiz: 7 kunlik (HAFTALIK) VARIATIV va FOYDALI taomlar ro'yxatini tuzish.
Har bir kun har xil bo'lishi SHART.

Javob formati: FAQAT JSON.

QAT'IY QOIDALAR:
1. Tilda aralashma bo'lmasin. FAQAT O'ZBEK TILI.
2. Mahsulotlar O'ZBEK BOZORIDA topiladigan bo'lsin.
3. Milliy taomlarni (yog'siz variantlarini) qo'shish tavsiya etiladi.
4. Taomlar takrorlanmasin (yoki kam takrorlansin).
"""

user_prompt = """
Ma'lumotlar:
Yosh: 25
Jins: Erkak
Maqsad: Ozish

Talablar:
- 7 kunlik reja (JSON array "menu" ichida). 
- DIQQAT: "menu" array ichida roppa-rosa 7 ta element bo'lishi SHART. Kam bo'lmasin.
- Har bir kun uchun: day, breakfast, lunch, dinner, snack.
- O'zbek milliy va yevropa taomlarini aralashtirib yoz.
- "shopping_list" da hamma kerakli mahsulotlar bo'lsin (faqat o'zbek tilida).
- JSON valid bo'lsin.
"""

full_text_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"

print("Running generation...")
try:
    response = model.generate_content(
        full_text_prompt,
        generation_config={"response_mime_type": "application/json"},
        request_options={'timeout': 120}
    )
    print("Response received.")
    print("Raw Text Length:", len(response.text))
    print("--- RAW CONTENT START ---")
    print(response.text)
    print("--- RAW CONTENT END ---")
    
    import json
    data = json.loads(response.text)
    print(f"Menu Items Count: {len(data['menu'])}")
    if len(data['menu']) < 7:
        print("FAIL: Generated fewer than 7 days.")
    else:
        print("SUCCESS: Generated 7 days.")
        
except Exception as e:
    print(f"Error: {e}")
