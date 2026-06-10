import os
import pytz

DEBUG = os.getenv("DEBUG", "false") == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL = os.getenv("REDIS_URL", "redis://$REDIS_HOST:$REDIS_PORT/0")
REFRESH_TOKEN_KEY = os.getenv("REFRESH_TOKEN_KEY", "refresh_token")
ACCESS_TOKEN_KEY = os.getenv("ACCESS_TOKEN_KEY", "access_token")
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-secret")
CREDENTIALS_ENCRYPTION_KEY = os.getenv("CREDENTIALS_ENCRYPTION_KEY", "")
EMAIL_SCAN_VERIFICATION_MODE = os.getenv("EMAIL_SCAN_VERIFICATION_MODE", "false") == "true"
EMAIL_SCAN_ALLOWED_EMAILS = {
    email.strip().lower() for email in os.getenv("EMAIL_SCAN_ALLOWED_EMAILS", "").split(",") if email.strip()
}
EMAIL_SCAN_VERIFICATION_REMITENTS = {
    remitent.strip().lower()
    for remitent in os.getenv("EMAIL_SCAN_VERIFICATION_REMITENTS", "").split(",")
    if remitent.strip()
}
WEB_ADDRESS = os.getenv("WEB_ADDRESS", "http://localhost:5173")
APP_NAME = "finitum"
TZ = pytz.timezone("America/Santiago")

# Inbound forwarding ingestion (Phase 2).
# Full mail domain for per-user ingest addresses: u-<token>@<INGEST_DOMAIN>.
# Use the apex (e.g. finitum.app) with Cloudflare Email Routing on the apex.
INGEST_DOMAIN = os.getenv("INGEST_DOMAIN", "finitum.app")
# Shared secret used to HMAC-sign the inbound webhook body (set on the CF worker too).
INGEST_WEBHOOK_SECRET = os.getenv("INGEST_WEBHOOK_SECRET", "")
# Legacy Gmail API polling path. Disabled by default now that forwarding ingestion exists.
GMAIL_POLLING_ENABLED = os.getenv("GMAIL_POLLING_ENABLED", "false") == "true"
