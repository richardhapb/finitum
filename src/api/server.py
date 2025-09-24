import os
from typing import Any
from fastapi import FastAPI, Request, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from api.jwt import create_access_token, create_refresh_token, get_current_user

from db.service import get_session
from sqlmodel import Session, or_, select
from db.models import (
    Expense as DBExpense,
    User,
    UserCreate,
    UserGoogleCredential,
    UserLoginResponse,
    UserResponse,
    UserLogin,
)
from fastapi.responses import RedirectResponse
from oauth_service import google_oauth
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from utils.logger import get_logger


logger = get_logger()


@asynccontextmanager
async def lifespan(app_service: FastAPI):
    """Application lifespan manager"""
    # Startup
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
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-insecure-change-me"),
    session_cookie="session",
    same_site="lax",  # or "none" if cross-site (requires HTTPS)
    https_only=False,  # set True in prod behind HTTPS
    max_age=60 * 60 * 24,  # 1 day
)


@app.get("/health", response_class=JSONResponse)
async def health() -> JSONResponse:
    return JSONResponse(status_code=200, content={"message": "OK"})


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
def signin(user_data: UserLogin, session: Session = Depends(get_session)) -> Any:
    existing_user = session.exec(
        select(User).where(or_(User.email == user_data.email, User.username == user_data.username))
    ).first()

    field = "email" if user_data.email else "username"
    logger.info("Trying to login: %s", field)

    if not existing_user:
        msg = f"User with this {field} doesn't exist"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    if not existing_user.verify_password(user_data.password):
        msg = "Incorrect password"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    data = {"sub": str(existing_user.username)}
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)

    logger.info("Logged in successfully")
    return {"user": existing_user, "access_token": access_token, "refresh_token": refresh_token}


@app.get("/expenses")
def get_expenses(
    request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    credentials = try_get_credentials(request, session)
    if not credentials:
        logger.info("Credentials not found in session, requesting authorization")
        return RedirectResponse("/google-authorize")

    expenses = session.exec(select(DBExpense)).all()
    return JSONResponse(content={"expenses": [expense.model_dump() for expense in expenses]})


@app.get("/google-authorize")
def auth_google(request: Request):
    auth_url, state = google_oauth.authorize_oauth2()
    request.session["state"] = state
    return RedirectResponse(auth_url)


@app.get("/google_oauth2callback")
def google_callback(request: Request, _code: str, state: str):
    stored_state = request.session.get("state", "")
    if state != stored_state:
        return JSONResponse(status_code=400, content={"error": "State mismatch"})

    # Construct the full authorization URL that Google redirected to
    authorization_url = str(request.url)
    credentials, features = google_oauth.get_credentials(state, authorization_url)

    request.session["credentials"] = credentials
    request.session["features"] = features
    return RedirectResponse("/expenses")


def try_get_credentials(request: Request, session: Session) -> dict[str, str | None] | None:
    if "credentials" in request.session:
        return request.session["credentials"]

    # Try to get from database
    user = try_get_user(request, session)
    if not user:
        return None

    credentials = session.get(UserGoogleCredential, {"user": user})
    if credentials:
        credentials_dict = google_oauth.credentials_to_dict(credentials)
        request.session["credentials"] = credentials_dict

        return credentials_dict

    return None


def try_get_user(request: Request, session: Session) -> User | None:
    if "user_id" not in request.session:
        return None

    try:
        user_id = int(request.session.get("user_id", "-"))
    except ValueError:
        return None

    return session.get(User, user_id)
