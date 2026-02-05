from tasks.email_fetch import get_user_messages
import json
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, cast

import jwt
import redis
from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import Session, or_, select
from starlette.middleware.cors import CORSMiddleware

from api.jwt import Token, get_current_user, set_access_cookie, set_refresh_cookie
from db.models import (
    Expense as DBExpense,
    UserUpdate,
)
from db.models import (
    ExpenseCreate,
    User,
    UserCreate,
    UserGoogleCredential,
    UserLogin,
    UserLoginResponse,
    UserResponse,
)
from db.service import get_session
from oauth_service import google_oauth
from utils.config import ACCESS_TOKEN_KEY, DEBUG, REDIS_HOST, REDIS_PORT, REFRESH_TOKEN_KEY
from utils.logger import get_logger

if TYPE_CHECKING:
    from starlette.middleware import _MiddlewareFactory

logger = get_logger()


@asynccontextmanager
async def lifespan(_app_service: FastAPI) -> AsyncGenerator[None]:  # noqa: RUF029
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

# CORS: Must use explicit origins when credentials are enabled (not "*")
_default_origins = "http://localhost:5173 http://localhost:9090 http://localhost:8081"
_allowed_origins = os.getenv("ALLOWED_ORIGINS", _default_origins).split()

app.add_middleware(
    cast("_MiddlewareFactory", CORSMiddleware),
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


@app.get("/health", response_class=JSONResponse)
async def health() -> JSONResponse:
    redis_status = "OK" if redis_client.ping() else "FAILED"
    return JSONResponse(status_code=200, content={"message": "OK", "redis": redis_status})


@app.get("/banks")
def get_available_banks() -> JSONResponse:
    """Get list of available banks for email parsing."""
    regex_path = os.path.join(os.path.dirname(__file__), "..", "parsers", "regex.json")
    with open(regex_path, encoding="utf-8") as f:
        banks_config = json.load(f)

    banks = [{"id": bank_id, "name": bank_id.replace("_", " ").title()} for bank_id in banks_config]
    return JSONResponse(content=banks)


@app.get("/debug/state")
async def debug_session() -> JSONResponse:
    if not DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content={"state": app.state.__dict__})


@app.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, session: Session = Depends(get_session)) -> User:
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
    new_user = User(username=user_data.username, email=user_data.email, bank=user_data.bank)
    new_user.set_password(user_data.password)

    # Save to database
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


@app.post("/signin", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
def signin(response: Response, user_data: UserLogin, session: Session = Depends(get_session)) -> dict[str, str | User]:
    existing_user = session.exec(
        select(User).where(or_(User.email == user_data.email, User.username == user_data.username))
    ).first()

    if not existing_user:
        field = "email" if user_data.email else "username"
        msg = f"User with this {field} doesn't exist"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    if not existing_user.password:
        msg = "User registered with google OAuth, init with google account instead"
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
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)

    logger.debug("Logged in successfully")
    response.status_code = status.HTTP_200_OK

    assert existing_user is not None

    return {
        "user": existing_user,
    }


@app.get("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(REFRESH_TOKEN_KEY)
    response.delete_cookie(ACCESS_TOKEN_KEY)

    return {"msg": "OK"}


@app.get("/me")
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Get current user info including Google credentials status."""
    return JSONResponse(
        content={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "bank": current_user.bank,
            "last_update": current_user.last_update.isoformat(),
            "has_google_credentials": current_user.google_credentials is not None,
            "is_google_credentials_valid": current_user.google_credentials.is_valid
            if current_user.google_credentials
            else False,
        }
    )


@app.patch("/me")
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Update current user's profile."""
    if user_update.username:
        # Check if username is taken
        existing = session.exec(
            select(User).where(User.username == user_update.username, User.id != current_user.id)
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        current_user.username = user_update.username

    if user_update.bank:
        current_user.bank = user_update.bank

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return JSONResponse(
        content={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "bank": current_user.bank,
            "last_update": current_user.last_update.isoformat(),
            "has_google_credentials": current_user.google_credentials is not None,
            "is_google_credentials_valid": current_user.google_credentials.is_valid
            if current_user.google_credentials
            else False,
        }
    )


@app.get("/expenses")
def get_expenses(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
) -> JSONResponse:
    """Get all expenses for the current user."""
    expenses = session.exec(select(DBExpense).where(DBExpense.user_id == current_user.id)).all()
    # Return array directly for easier frontend consumption
    return JSONResponse(content=[expense.model_dump(mode="json") for expense in expenses])


@app.post("/expenses", status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Create a new expense for the current user."""
    new_expense = DBExpense(
        user_id=current_user.id,
        commerce=expense_data.commerce,
        amount=expense_data.amount,
        currency=expense_data.currency,
        category=expense_data.category,
        date=expense_data.date if expense_data.date else datetime.now(),
        description=expense_data.description,
    )
    session.add(new_expense)
    session.commit()
    session.refresh(new_expense)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=new_expense.model_dump(mode="json"),
    )


@app.get("/google-authorize")
def auth_google() -> RedirectResponse:
    state = google_oauth.generate_oauth_state(redis_client)
    client = google_oauth.GoogleClient()
    auth_url, _ = client.authorize_oauth2(state=state)
    return RedirectResponse(auth_url)


@app.get("/google_oauth2callback")
def google_callback(
    request: Request,
    state: str,
    error: str | None = None,
    session: Session = Depends(get_session),
) -> Response:
    if error:
        logger.error("OAuth error: %s", error)
        raise HTTPException(status_code=400, detail=error)

    if not state or not google_oauth.validate_oauth_state(state, redis_client):
        logger.debug("Invalid state: %s", state)
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    client = google_oauth.GoogleClient()
    authorization_url = str(request.url)
    credentials_dict = client.get_credentials(state, authorization_url)

    id_token = credentials_dict.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="Missing id_token from Google")

    assert isinstance(id_token, str)
    decoded = jwt.decode(id_token, options={"verify_signature": False})

    email = decoded.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not present in Google token")

    user = session.exec(select(User).where(User.email == email)).first()

    if user:
        # Update the expenses of the user now because
        # is reactivated or new
        get_user_messages.delay(user.id)

    if not user:
        user = User(username=email, email=email)
        session.add(user)
        session.commit()
        session.refresh(user)

    save_credentials(user, credentials_dict, session)

    access = Token.create_access_token({"sub": user.username})
    refresh = Token.create_refresh_token({"sub": user.username})

    response = RedirectResponse("/dashboard")
    set_access_cookie(response, access)
    set_refresh_cookie(response, refresh)

    return response


@app.get("/session", response_model=dict, status_code=status.HTTP_200_OK)
def validate_session(_user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"msg": "OK"}


@app.post("/refresh", response_model=dict)
async def refresh_token(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Refresh access token using refresh token from cookie."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_KEY)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")

    new_access = await Token.refresh_access_token(refresh_token, session)
    set_access_cookie(response, new_access)

    return {}


def save_credentials(user: User, credentials: dict[str, str | list[str] | None], session: Session) -> None:
    logger.debug("Saving credentials to user: %s", user.username)

    # Prepare new credential data

    new_cred_data = {
        "user_id": user.id,
        "user": user,
        "token": str(credentials.get("token", "")),
        "refresh_token": str(credentials.get("refresh_token", "")),
        "token_uri": str(credentials.get("token_uri", "")),
        "client_id": str(credentials.get("client_id", "")),
        "client_secret": str(credentials.get("client_secret", "")),
        "scopes_json": json.dumps(credentials.get("scopes", [])),
        "granted_scopes_json": json.dumps(credentials.get("granted_scopes", [])),
        "expiry": datetime.fromisoformat(str(credentials["expiry"])) if credentials.get("expiry") else None,
        "id_token": str(credentials.get("id_token")) if credentials.get("id_token") else None,
        "is_valid": True,
    }

    # Check for existing credentials
    existing_cred = session.exec(select(UserGoogleCredential).where(UserGoogleCredential.user_id == user.id)).first()

    if existing_cred:
        logger.debug("Updating existing credentials for user: %s", user.username)
        for key, value in new_cred_data.items():
            if key != "user":  # Skip relationship field update to avoid conflicts
                setattr(existing_cred, key, value)
        session.add(existing_cred)
    else:
        logger.debug("Creating new credentials for user: %s", user.username)
        new_cred = UserGoogleCredential(**new_cred_data)
        session.add(new_cred)

    session.commit()
