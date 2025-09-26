import os
import secrets
from contextlib import asynccontextmanager
from typing import Any

import redis
from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import Session, or_, select
from starlette.middleware.cors import CORSMiddleware

from api.jwt import Token, get_current_user
from db.models import (
    Expense as DBExpense,
)
from db.models import (
    User,
    UserCreate,
    UserGoogleCredential,
    UserLogin,
    UserLoginResponse,
    UserResponse,
)
from db.service import get_session
from oauth_service import google_oauth
from utils.config import DEBUG, REDIS_HOST, REDIS_PORT, REFRESH_TOKEN_KEY
from utils.logger import get_logger

logger = get_logger()


@asynccontextmanager
async def lifespan(app_service: FastAPI):
    """Application lifespan manager"""
    # Startup
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" if DEBUG else "0"
    logger.info("Finance manager started")
    yield

    # Shutdown
    logger.info("Finance manager shutdown")


app = FastAPI(
    title="Finitum - Finance manager",
    description="Handle the expenses and manage finance elements",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "ALLOWED_ORIGINS", "http://0.0.0.0:9090 http://localhost:9090 http://127.0.0.1:9090"
    ).split(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


# Functions for state management
def generate_oauth_state() -> str:
    """Generate a unique state token and store it in Redis with expiration."""
    state = secrets.token_urlsafe(32)
    # Store in Redis with 10 minute expiration
    redis_client.setex(f"oauth_state:{state}", 600, "1")
    return state


def validate_oauth_state(state: str) -> bool:
    """Validate a state token from Redis and delete it if valid."""
    key = f"oauth_state:{state}"
    valid = redis_client.exists(key)
    if valid:
        # Delete after use (one-time use)
        redis_client.delete(key)
    return bool(valid)


@app.get("/health", response_class=JSONResponse)
async def health() -> JSONResponse:
    redis_status = "OK" if redis_client.ping() else "FAILED"
    return JSONResponse(status_code=200, content={"message": "OK", "redis": redis_status})


@app.get("/debug/state")
async def debug_session():
    if not DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content={"state": app.state.__dict__})


@app.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, session: Session = Depends(get_session)) -> Any:
    """
    Register a new user in the system.

    Args:
        user_data: User registration data containing username, email and password
        session: Database session

    Returns:
        The newly created user object (password excluded)

    Raises:
        HTTPException: If email/username already exists
    """
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(or_(User.email == user_data.email, User.username == user_data.username))
    ).first()

    if existing_user:
        field = "email" if existing_user.email == user_data.email else "username"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User with this {field} already exists")

    # Create new user object
    new_user = User(username=user_data.username, email=user_data.email)
    new_user.set_password(user_data.password)

    # Save to database
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


@app.post("/signin", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
def signin(request: Request, response: Response, user_data: UserLogin, session: Session = Depends(get_session)) -> Any:
    existing_user = session.exec(
        select(User).where(or_(User.email == user_data.email, User.username == user_data.username))
    ).first()

    if not existing_user:
        field = "email" if user_data.email else "username"
        msg = f"User with this {field} doesn't exist"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    logger.debug("Trying to login: %s", existing_user.username)

    if not existing_user.verify_password(user_data.password):
        msg = "Incorrect password"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    data = {"sub": str(existing_user.username)}
    access_token = Token.create_access_token(data=data)
    refresh_token = Token.create_refresh_token(data=data)

    logger.debug("Setting refresh_token cookie")
    response.set_cookie(
        key=REFRESH_TOKEN_KEY,
        value=refresh_token.token,
        httponly=True,
        secure=not DEBUG,  # Only send over HTTPS
        samesite="lax",  # Helps prevent CSRF attacks
        expires=refresh_token.exp,
    )

    logger.debug("Logged in successfully")
    response.status_code = status.HTTP_200_OK

    response.status_code = status.HTTP_200_OK

    return {
        "user": existing_user,
        "access_token": access_token.token,
        "token_type": "bearer",
    }


@app.get("/expenses")
def get_expenses(
    request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    expenses = session.exec(select(DBExpense)).all()
    return JSONResponse(content={"expenses": [expense.model_dump() for expense in expenses]})


@app.get("/google-authorize")
def auth_google(
    current_user: User = Depends(get_current_user),
):
    state = generate_oauth_state()
    auth_url, _ = google_oauth.authorize_oauth2(state=state)
    return RedirectResponse(auth_url)


@app.get("/google_oauth2callback")
def google_callback(
    request: Request,
    state: str,
    error: str | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Check for OAuth errors
    if error:
        logger.error(f"OAuth error: {error}")
        return JSONResponse(status_code=400, content={"error": error})

    # Validate state using Redis
    if not state or not validate_oauth_state(state):
        logger.debug(f"Invalid state: {state}")
        return JSONResponse(status_code=400, content={"error": "Invalid state parameter"})

    # State is valid, continue with OAuth flow
    authorization_url = str(request.url)
    credentials = google_oauth.get_credentials(state, authorization_url)

    save_credentials(current_user, credentials, session)

    return RedirectResponse("/expenses")


def save_credentials(user: User, credentials: dict[str, str | list[str] | None], session: Session) -> None:
    logger.debug("Saving credentials to user: %s", user)

    new_cred = UserGoogleCredential(
        user_id=user.id if user.id else 0,
        user=user,
        granted_scopes=",".join(list(credentials["granted_scopes"] if credentials["granted_scopes"] else [])),
        token=str(credentials["token"]),
        refresh_token=str(credentials["refresh_token"]),
    )

    session.add(new_cred)
    session.commit()
