import os

DEBUG = os.getenv("DEBUG", "false") == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL = os.getenv("REDIS_URL", "redis://$REDIS_HOST:$REDIS_PORT/0")
REFRESH_TOKEN_KEY=os.getenv("REFRESH_TOKEN_KEY", "refresh_token")
APP_NAME = "finitum"

