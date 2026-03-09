from core.content import content_manager

defaults = {
    "premium_title": "💎 **Premium Bo'limi**",
    "premium_desc": "Premium imkoniyatlari:\n• Cheksiz AI maslahatlari\n• Foto orqali kaloriya aniqlash\n• Chellenjlarda 2x ball",
    "welcome_message": "Assalomu alaykum! YASHA Fitness Botiga xush kelibsiz.",
    "onboarding_name": "Ismingizni kiriting:",
    "onboarding_age": "Yoshingizni kiriting (faqat raqam):"
}

print("Seeding default content...")
for key, value in defaults.items():
    if not content_manager.get(key):
        content_manager.set(key, value)
        print(f"Set default for {key}")
    else:
        print(f"Skipped {key} (already exists)")

print("Done.")
