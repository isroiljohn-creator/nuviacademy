import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "YASHA Fitness Bot"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ CRITICAL: BOT_TOKEN is missing!")
        raise RuntimeError("BOT_TOKEN is required.")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", 0))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # Payments
    CLICK_SERVICE_ID: str = os.getenv("CLICK_SERVICE_ID")
    CLICK_MERCHANT_ID: str = os.getenv("CLICK_MERCHANT_ID")
    CLICK_SECRET_KEY: str = os.getenv("CLICK_SECRET_KEY")
    
    PAYME_ID: str = os.getenv("PAYME_ID")
    PAYME_KEY: str = os.getenv("PAYME_KEY")

settings = Settings()
