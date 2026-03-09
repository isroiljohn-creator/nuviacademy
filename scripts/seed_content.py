from core.content import content_manager

defaults = {
    # Welcome & Onboarding
    "welcome_message": "👋 Assalomu alaykum! YASHA Fitness Botiga xush kelibsiz.\n\nMen sizga sog'lom turmush tarziga erishishda yordam beraman! 💪",
    "onboarding_name": "📝 Ismingizni kiriting:",
    "onboarding_age": "🎂 Yoshingizni kiriting (faqat raqam):",
    "onboarding_gender": "👥 Jinsingizni tanlang:",
    "onboarding_height": "📏 Bo'yingizni kiriting (sm):",
    "onboarding_weight": "⚖️ Vazningingizni kiriting (kg):",
    "onboarding_goal": "🎯 Maqsadingizni tanlang:",
    "onboarding_activity": "🏃 Faollik darajangizni tanlang:",
    "onboarding_complete": "✅ Ro'yxatdan o'tish yakunlandi!\n\nEndi siz barcha funksiyalardan foydalanishingiz mumkin. Omad! 🎉",
    
    # Main Menu
    "main_menu_title": "🏠 Asosiy menyu",
    "main_menu_desc": "Quyidagi bo'limlardan birini tanlang:",
    
    # Premium
    "premium_title": "💎 Premium Bo'limi",
    "premium_desc": "Premium imkoniyatlari:\n\n• ♾️ Cheksiz AI maslahatlari\n• 📸 Foto orqali kaloriya aniqlash\n• 🏆 Chellenjlarda 2x ball\n• 🎯 Maxsus mashg'ulotlar rejasi\n• 📊 Batafsil statistika",
    "premium_price": "💰 Narx: 50,000 so'm/oy",
    "premium_subscribe": "Premium obunani faollashtirish uchun to'lov qiling.",
    "premium_active": "✅ Sizda Premium obuna faol!\n\nAmal qilish muddati: {date}",
    "premium_required": "⚠️ Bu funksiya faqat Premium foydalanuvchilar uchun mavjud.\n\n💎 Premium obunani sotib oling!",
    
    # Workout
    "workout_title": "🏋️ Mashqlar",
    "workout_menu": "Mashqlar bo'limiga xush kelibsiz!\n\nQuyidagi variantlardan birini tanlang:",
    "workout_ai_generating": "⏳ AI sizga maxsus mashqlar rejasini tayyorlayapti...\n\nBir oz sabr qiling! 🤖",
    "workout_ai_success": "✅ Mashqlar rejangiz tayyor!",
    "workout_ai_error": "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
    "workout_daily_empty": "📋 Bugungi reja hali mavjud emas.\n\nAI dan mashqlar rejasini yaratishingiz mumkin!",
    
    # Nutrition
    "nutrition_title": "🥗 Ovqatlanish",
    "nutrition_menu": "Ovqatlanish bo'limiga xush kelibsiz!\n\nQuyidagi variantlardan birini tanlang:",
    "nutrition_ai_generating": "⏳ AI sizga ovqatlanish rejasini tayyorlayapti...\n\nBir oz sabr qiling! 🤖",
    "nutrition_ai_success": "✅ Ovqatlanish rejangiz tayyor!",
    "nutrition_ai_error": "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
    "nutrition_daily_empty": "📋 Bugungi ovqat rejasi hali mavjud emas.\n\nAI dan ovqat rejasini yaratishingiz mumkin!",
    
    # Profile
    "profile_title": "👤 Profil",
    "profile_view": "📊 Sizning profilingiz:",
    "profile_edit": "✏️ Profilni tahrirlash uchun quyidagi parametrlardan birini tanlang:",
    "profile_updated": "✅ Profil yangilandi!",
    
    # Gamification
    "gamification_title": "🎮 Motivatsiya",
    "points_earned": "🎉 Siz {points} ball oldingiz!",
    "level_up": "🎊 Tabriklaymiz! Siz {level} darajaga ko'tarildingiz!",
    "daily_streak": "🔥 Sizning seriyangiz: {days} kun!",
    "challenge_complete": "🏆 Chellenj yakunlandi! +{points} ball",
    
    # Referral
    "referral_title": "🔗 Do'stlarni taklif qiling",
    "referral_desc": "Do'stingizni taklif qilib, sovg'alar qo'lga kiriting!\n\n• Har bir do'st uchun: +100 ball\n• Do'stingiz Premium olsa: +500 ball",
    "referral_link": "🔗 Sizning referral havolangiz:\n{link}\n\nTaklif qilganlar: {count} ta",
    
    # Calorie Scanner
    "calorie_title": "📸 Kaloriya skaneri",
    "calorie_prompt": "Ovqat rasmini yuboring, men kaloriyalarni hisoblayman! 📷",
    "calorie_analyzing": "🔍 Rasm tahlil qilinmoqda...",
    "calorie_result": "📊 Natija:\n\n{result}",
    
    # Errors & Messages
    "error_generic": "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
    "error_invalid_input": "⚠️ Noto'g'ri ma'lumot. Qaytadan kiriting.",
    "success_generic": "✅ Muvaffaqiyatli!",
    "loading": "⏳ Yuklanmoqda...",
    "please_wait": "⏰ Iltimos, bir oz kuting...",
    
    # Admin
    "admin_panel_title": "👨‍💼 Admin Panel",
    "admin_stats_title": "📊 Statistika",
    "admin_users_title": "👥 Foydalanuvchilar",
    "admin_broadcast_title": "📨 Umumiy xabar",
}

print("Seeding default content...")
for key, value in defaults.items():
    if not content_manager.get(key):
        content_manager.set(key, value)
        print(f"✅ Set default for {key}")
    else:
        print(f"⏭️  Skipped {key} (already exists)")

print("\n🎉 Done! Total texts: " + str(len(defaults)))
