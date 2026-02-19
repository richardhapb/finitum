import os
import pytz

DEBUG = os.getenv("DEBUG", "false") == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL = os.getenv("REDIS_URL", "redis://$REDIS_HOST:$REDIS_PORT/0")
REFRESH_TOKEN_KEY = os.getenv("REFRESH_TOKEN_KEY", "refresh_token")
ACCESS_TOKEN_KEY = os.getenv("ACCESS_TOKEN_KEY", "access_token")
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-secret")
EMAIL_SCAN_VERIFICATION_MODE = os.getenv("EMAIL_SCAN_VERIFICATION_MODE", "false") == "true"
EMAIL_SCAN_ALLOWED_EMAILS = {
    email.strip().lower() for email in os.getenv("EMAIL_SCAN_ALLOWED_EMAILS", "").split(",") if email.strip()
}
EMAIL_SCAN_VERIFICATION_REMITENTS = {
    remitent.strip().lower() for remitent in os.getenv("EMAIL_SCAN_VERIFICATION_REMITENTS", "").split(",") if remitent.strip()
}
APP_NAME = "finitum"
TZ = pytz.timezone("America/Santiago")
