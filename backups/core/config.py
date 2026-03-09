import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Configuration")

load_dotenv()

def get_env_required(key):
    value = os.getenv(key)
    if not value:
        logger.error(f"Missing required environment variable: {key}")
        # We allow SQLite fallback for local dev if explicitly requested or if we want to be lenient
        # But per requirements "fail fast", we should probably be strict or at least loud.
        # Let's be strict for critical keys unless a default is provided.
        return None
    return value

# Bot Config
BOT_TOKEN = get_env_required("BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("BOT_TOKEN is missing! Bot cannot start.")
    sys.exit(1)

WEBAPP_URL = os.getenv("WEBAPP_URL")

# Database
# Requirement: "If DATABASE_URL is missing or invalid, the app fails fast"
# But also: "SQLite in local/dev if needed"
# Approach: Require DATABASE_URL to be set. If user wants SQLite, they set DATABASE_URL=sqlite:///...
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.critical("DATABASE_URL must be set! Exiting.")
    sys.exit(1)
else:
    if "sqlite" in DATABASE_URL:
        logger.critical("SQLite is NOT allowed in production! Use PostgreSQL.")
        sys.exit(1)
    logger.info(f"Database URL configured: {DATABASE_URL.split('://')[0]}://...")

# AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is missing! AI features will be disabled or fail.")

# Admin
# Parse ADMIN_ID (single) and ADMIN_IDS (comma separated list)
ADMIN_IDS = []
try:
    # Legacy single ID
    main_admin = os.getenv("ADMIN_ID")
    if main_admin and main_admin.strip().isdigit():
        ADMIN_IDS.append(int(main_admin))
    
    # List of IDs
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        for x in admin_ids_str.split(","):
            if x.strip().isdigit():
                ADMIN_IDS.append(int(x.strip()))
    
    # Deduplicate
    ADMIN_IDS = list(set(ADMIN_IDS))

    # Explicitly add requested admin
    if 6770204468 not in ADMIN_IDS:
        ADMIN_IDS.append(6770204468)
    if 1392501306 not in ADMIN_IDS:
        ADMIN_IDS.append(1392501306)
    
    if not ADMIN_IDS:
        logger.warning("No ADMIN_IDS configured! Admin features will be inaccessible.")
    else:
        logger.info(f"Loaded {len(ADMIN_IDS)} Admin IDs.")
        
except Exception as e:
    logger.error(f"Error parsing ADMIN_IDS: {e}")

# Payment
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

# Premium Prices (in tiyin)
PRICE_1_MONTH = 4900000 # 49,000 UZS
PRICE_3_MONTHS = 11900000 # 119,000 UZS

