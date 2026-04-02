"""
SmartSafety+ - Configuration and Database
Centralized configuration with validation for all modules.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import HTTPBearer
from pathlib import Path
from dotenv import load_dotenv
import os
import logging
import sys

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ── Logging (structured) ────────────────────────────────────────
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("smartsafety")

# ── MongoDB ──────────────────────────────────────────────────────
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

# ── JWT ──────────────────────────────────────────────────────────
JWT_SECRET = os.environ.get('JWT_SECRET', 'smartsafety_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '24'))
security = HTTPBearer()

# Warn if using default secret
if JWT_SECRET == 'smartsafety_secret_key':
    logger.warning("⚠️  Using default JWT_SECRET — change this in production!")

# ── LLM ──────────────────────────────────────────────────────────
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
if not EMERGENT_LLM_KEY:
    logger.warning("⚠️  EMERGENT_LLM_KEY not set — AI features (Scan360, Chat, Predictions) disabled")

# ── Email (Resend) ───────────────────────────────────────────────
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

import resend as _resend
if RESEND_API_KEY:
    _resend.api_key = RESEND_API_KEY
    logger.info("✅ Email service (Resend) configured")
else:
    logger.info("ℹ️  Email not configured (RESEND_API_KEY)")
resend = _resend

# ── SMS (Twilio) ─────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client as TwilioClient
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("✅ SMS service (Twilio) configured")
    except ImportError:
        logger.info("ℹ️  Twilio package not installed — SMS disabled")
    except Exception as e:
        logger.warning(f"⚠️  Twilio init failed: {e}")

# ── Uploads ──────────────────────────────────────────────────────
UPLOADS_DIR = ROOT_DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True)
(UPLOADS_DIR / 'scans').mkdir(exist_ok=True)

# ── Startup summary ─────────────────────────────────────────────
logger.info(f"🚀 SmartSafety+ config loaded | DB: {DB_NAME} @ {MONGO_URL.split('@')[-1] if '@' in MONGO_URL else MONGO_URL}")
