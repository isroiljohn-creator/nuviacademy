from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'OMMAVIY OFERTA (Foydalanish shartlari)', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Sahifa {self.page_no()}', 0, 0, 'C')

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

text = """
1. UMUMIY QOIDALAR

1.1. Mazkur hujjat "Yasha AI Bot" (keyingi o'rinlarda "Bot") xizmatlaridan foydalanish bo'yicha ommaviy oferta hisoblanadi.
1.2. Botdan foydalanishni boshlash, ro'yxatdan o'tish yoki to'lovni amalga oshirish ushbu Oferta shartlarini to'liq va so'zsiz qabul qilishni anglatadi.

2. XIZMATLAR TAVSIFI

2.1. Bot foydalanuvchilarga sun'iy intellekt yordamida sog'lom turmush tarzi bo'yicha maslahatlar, ovqatlanish rejalari va mashqlar dasturlarini taqdim etadi.
2.2. Bot tibbiy xizmat ko'rsatmaydi. Barcha maslahatlar tavsiyaviy xarakterga ega. Sog'liq bilan bog'liq jiddiy masalalarda shifokor bilan maslahatlashish zarur.

3. TO'LOV VA OBUNA SHARTLARI

3.1. Botning ayrim xizmatlari pullik (Premium va VIP tariflar).
3.2. To'lovlar Telegram Payment, Click, Payme yoki Uzum orqali amalga oshiriladi.
3.3. Raqamli tovarlar va xizmatlar sifatidan qoniqmagan taqdirda, to'lov qaytarilmaydi (refund qilinmaydi), agar xizmat ko'rsatishda texnik xatolik yuz bermagan bo'lsa.
3.4. Obuna muddati tugagach, xizmat ko'rsatish avtomatik ravishda to'xtatiladi yoki bepul tarifga o'tkaziladi.

4. MULLIFLIK HUQUQLARI

4.1. Botdagi barcha materiallar mualliflik huquqi bilan himoyalangan. Ularni ruxsatsiz tarqatish yoki tijoriy maqsadda foydalanish taqiqlanadi.

5. JAVOBGARLIKNI CHEKLASH

5.1. Bot ma'muriyati foydalanuvchi tomonidan kiritilgan noto'g'ri ma'lumotlar yoki maslahatlarga noto'g'ri amal qilish oqibatida kelib chiqqan zararlar uchun javobgar emas.
5.2. Botning uzluksiz ishlashiga kafolat berilmaydi, lekin ma'muriyat buning uchun barcha choralarni ko'radi.

6. BOG'LANISH

Murojaat uchun: @admin
Sana: 2025 yil 12 dekabr
"""

# Handling Unicode/Encoding issues with FPDF simply by replacing potentially problematic chars if standard font doesn't support basic ascii. 
# Actually Helvetica standard font doesn't support Uzbek chars like 'o' or 'g' with marks properly sometimes? 
# Standard fonts support some accents but "o'" and "g'" are just apostrophes in Uzbek Latin usually.
# However, if I use special chars, I might need a Unicode font.
# To be safe and quick, I will replace unicode apostrophes with simple ones and ensure text is clean.
# FPDF standard fonts are latin-1 usually. Uzbek latin is mostly latin-1 compatible except strictly standard apostrophe.

# Let's try to add a unicode font if possible, OR just use standard font and transliterate if needed.
# Since I cannot easily download a ttf font right now without internet access to font repo (I assume I have no external access except allowed tools), I will try to use standard Helvetica and ensure text is ASCII-friendly or use the `fpdf2` unicode capabilities if it comes with a font. `fpdf2` has better execution.

# Actually `fpdf2` replaced `fpdf` and supports unicode better but needs a font file.
# I will check if there is any ttf on system or just stick to simple text.
# Let's output straightforward text.

# Using latin-1 encoding for simplicity as 'fpdf' defaults to latin-1.
# I'll replace fancy quotes.
text = text.replace("‘", "'").replace("’", "'")

try:
    pdf.multi_cell(0, 10, text)
    pdf.output("assets/offerta.pdf")
    print("PDF Generated Successfully")
except Exception as e:
    print(f"Error: {e}")
