import json
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

import google.auth.transport.requests
import redis
from fastapi import Depends, FastAPI, Query, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth.exceptions import GoogleAuthError
from google.oauth2 import id_token as google_id_token
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from slowapi import Limiter, _rate_limit_exceeded_handler  # noqa: PLC2701
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlmodel import Session, or_, select
from starlette.middleware.cors import CORSMiddleware

from api.jwt import Token, get_current_user, set_access_cookie, set_refresh_cookie
from db.categories import (
    create_custom_category,
    get_category_patterns,
    get_global_category_by_slug,
    get_visible_category,
    list_categories_for_user,
)
from db.models import (
    Category,
    CategoryCreate,
    CategoryRead,
    Expense as DBExpense,
    ExpenseRead,
    Transference as DBTransference,
    TransferenceRead,
)
from db.models import (
    ExpenseCreate,
    User,
    UserCreate,
    UserGoogleCredential,
    UserLogin,
    UserLoginResponse,
    UserResponse,
    UserUpdate,
)
from db.service import get_session
from email_service import ingest
from oauth_service import google_oauth
from tasks.email_fetch import get_user_messages
from utils.config import (
    ACCESS_TOKEN_KEY,
    DEBUG,
    EMAIL_SCAN_ALLOWED_EMAILS,
    EMAIL_SCAN_VERIFICATION_MODE,
    GMAIL_POLLING_ENABLED,
    INGEST_DOMAIN,
    INGEST_WEBHOOK_SECRET,
    REDIS_HOST,
    REDIS_PORT,
    REFRESH_TOKEN_KEY,
    WEB_ADDRESS,
)
from utils.crypto import encrypt
from utils.logger import get_logger

if TYPE_CHECKING:
    from starlette.middleware import _MiddlewareFactory

logger = get_logger()


@asynccontextmanager
async def lifespan(_app_service: FastAPI) -> AsyncGenerator[None]:  # noqa: RUF029
    """Application lifespan manager"""
    # Startup
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" if DEBUG else "0"
    # Allow Google to grant fewer scopes than requested (e.g. user unchecks Gmail)
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"  # noqa: S105
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

# Rate limiting (per client IP) for sensitive auth endpoints.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: Must use explicit origins when credentials are enabled (not "*")
_default_origins = "http://localhost:5173 http://localhost:9090 http://localhost:8081"
_allowed_origins = os.getenv("ALLOWED_ORIGINS", _default_origins).split()

app.add_middleware(
    cast("_MiddlewareFactory", CORSMiddleware),
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


def can_use_verification_scan(user: User) -> bool:
    """Restrict manual scan controls to verification mode (and optional allowlist)."""
    if not EMAIL_SCAN_VERIFICATION_MODE:
        return False
    if not EMAIL_SCAN_ALLOWED_EMAILS:
        return True
    return user.email.lower() in EMAIL_SCAN_ALLOWED_EMAILS


def serialize_category(category: Category, patterns: list[str] | None = None) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        slug=category.slug,
        name=category.name_es,
        name_en=category.name_en,
        name_es=category.name_es,
        is_custom=category.user_id is not None,
        patterns=patterns or [],
    )


def serialize_expense(expense: DBExpense, category: Category) -> ExpenseRead:
    return ExpenseRead(
        id=expense.id,
        user_id=expense.user_id,
        commerce=expense.commerce,
        amount=expense.amount,
        currency=expense.currency,
        category_id=expense.category_id,
        category_slug=category.slug,
        category_name=category.name_es,
        category_is_custom=category.user_id is not None,
        date=expense.date,
        description=expense.description,
    )


def serialize_transference(transference: DBTransference, category: Category) -> TransferenceRead:
    return TransferenceRead(
        id=transference.id,
        user_id=transference.user_id,
        recipient=transference.recipient,
        amount=transference.amount,
        currency=transference.currency,
        category=transference.category,
        category_slug=category.slug,
        category_name=category.name_es,
        date=transference.date,
        description=transference.description,
    )


def serialize_user_info(user: User) -> dict[str, object]:
    """Build the /me payload, including forwarding ingestion status."""
    creds = user.google_credentials
    ingest_address = ingest.build_ingest_address(user.ingest_token, INGEST_DOMAIN) if user.ingest_token else None
    last_email_at = ingest.get_last_email_at(redis_client, user.id) if user.id is not None else None
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bank": user.bank,
        "last_update": user.last_update.isoformat(),
        "has_google_credentials": creds is not None,
        "is_google_credentials_valid": creds.is_valid if creds else False,
        # Forwarding ingestion status (replaces has_gmail_scope).
        "ingest_address": ingest_address,
        "forwarding_active": last_email_at is not None,
        "last_email_received_at": last_email_at,
        "verification_scan_enabled": can_use_verification_scan(user),
    }


def require_user_id(user: User) -> int:
    if user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authenticated user is invalid")
    return user.id


@app.get("/health", response_class=JSONResponse)
async def health() -> JSONResponse:
    try:
        redis_ok = bool(redis_client.ping())
    except redis.RedisError:
        logger.exception("Redis health check failed")
        redis_ok = False

    if not redis_ok:
        return JSONResponse(status_code=503, content={"message": "FAILED", "redis": "FAILED"})
    return JSONResponse(status_code=200, content={"message": "OK", "redis": "OK"})


@app.get("/banks")
def get_available_banks() -> JSONResponse:
    """Get list of available banks for email parsing."""
    regex_path = os.path.join(os.path.dirname(__file__), "..", "parsers", "regex.json")
    with open(regex_path, encoding="utf-8") as f:
        banks_config = json.load(f)

    banks = [
        {
            "id": bank_id,
            "name": bank_id.replace("_", " ").title(),
            "senders": config.get("remitents", []),
        }
        for bank_id, config in banks_config.items()
    ]
    return JSONResponse(content=banks)


@app.get("/debug/state")
async def debug_session() -> JSONResponse:
    if not DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content={"state": app.state.__dict__})


@app.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, user_data: UserCreate, session: Session = Depends(get_session)) -> User:  # noqa: ARG001
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
@limiter.limit("5/minute")
def signin(
    request: Request,  # noqa: ARG001
    response: Response,
    user_data: UserLogin,
    session: Session = Depends(get_session),
) -> dict[str, str | User]:
    invalid_credentials = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials"
    )

    existing_user = session.exec(
        select(User).where(or_(User.email == user_data.email, User.username == user_data.username))
    ).first()

    if not existing_user:
        field = "email" if user_data.email else "username"
        logger.error("User with this %s doesn't exist", field)
        raise invalid_credentials

    if not existing_user.password:
        logger.error("User %s registered with google OAuth, init with google account instead", existing_user.username)
        raise invalid_credentials

    logger.debug("Trying to login: %s", existing_user.username)

    if not existing_user.verify_password(user_data.password):
        logger.error("Incorrect password for user %s", existing_user.username)
        raise invalid_credentials

    data = {"sub": str(require_user_id(existing_user))}
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
    """Get current user info including Google credentials and forwarding status."""
    return JSONResponse(content=serialize_user_info(current_user))


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

    return JSONResponse(content=serialize_user_info(current_user))


@app.get("/ingest/address")
def get_ingest_address(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Return the user's inbound forwarding address, generating the token lazily."""
    if not current_user.ingest_token:
        # Generate a unique token, retrying on the rare collision.
        for _ in range(5):
            candidate = User.generate_ingest_token()
            if session.exec(select(User).where(User.ingest_token == candidate)).first() is None:
                current_user.ingest_token = candidate
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not allocate ingest token"
            )
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

    address = ingest.build_ingest_address(current_user.ingest_token, INGEST_DOMAIN)
    return JSONResponse(content={"address": address})


@app.get("/ingest/confirmation")
def get_ingest_confirmation(current_user: User = Depends(get_current_user)) -> JSONResponse:
    """Return the captured Gmail forwarding confirmation link/code, if any."""
    if not current_user.ingest_token:
        return JSONResponse(content={"confirmation": None})
    confirmation = ingest.get_confirmation(redis_client, current_user.ingest_token)
    return JSONResponse(content={"confirmation": confirmation})


@app.post("/ingest/email")
async def ingest_email(
    request: Request,
    recipient: str = Query(..., description="Destination ingest address u-<token>@in.<domain>"),
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Inbound webhook for forwarded bank emails (called by the CF Email worker).

    The body is the raw MIME message; ``X-Finitum-Signature`` is its HMAC-SHA256.
    Always returns 200 on a valid signature (even for unknown tokens) so the
    worker never retries in a way that leaks which tokens are valid.
    """
    body = await request.body()
    signature = request.headers.get("X-Finitum-Signature")
    if not ingest.verify_signature(INGEST_WEBHOOK_SECRET, body, signature):
        logger.warning("Rejected inbound email with invalid signature for recipient %r", recipient)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    result = ingest.process_inbound_email(body, recipient, session=session, redis_client=redis_client)
    return JSONResponse(content={"status": result.outcome.value})


@app.get("/categories", response_model=list[CategoryRead])
def get_categories(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[CategoryRead]:
    categories = list_categories_for_user(session, require_user_id(current_user))
    category_ids = [category.id for category in categories if category.id is not None]
    patterns_by_category_id = get_category_patterns(session, category_ids)
    return [
        serialize_category(category, patterns_by_category_id.get(category.id or 0, []))
        for category in categories
    ]


@app.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> CategoryRead:
    try:
        category = create_custom_category(session, require_user_id(current_user), category_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    patterns_by_category_id = get_category_patterns(session, [category.id] if category.id is not None else [])
    return serialize_category(category, patterns_by_category_id.get(category.id or 0, []))


@app.get("/expenses", response_model=list[ExpenseRead])
def get_expenses(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ExpenseRead]:
    """Get expenses for the current user, most recent first."""
    user_id = require_user_id(current_user)
    expenses = session.exec(
        select(DBExpense, Category)
        .join(Category, DBExpense.category_id == Category.id)
        .where(DBExpense.user_id == user_id)
        .order_by(DBExpense.date.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [serialize_expense(expense, category) for expense, category in expenses]


@app.post("/expenses", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ExpenseRead:
    """Create a new expense for the current user."""
    user_id = require_user_id(current_user)
    category = get_visible_category(session, expense_data.category_id, user_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Category is invalid")

    new_expense = DBExpense(
        user_id=user_id,
        commerce=expense_data.commerce,
        amount=expense_data.amount,
        currency=expense_data.currency,
        category_id=category.id,
        date=expense_data.date if expense_data.date else datetime.now(UTC),
        description=expense_data.description,
    )
    session.add(new_expense)
    session.commit()
    session.refresh(new_expense)
    return serialize_expense(new_expense, category)


@app.delete("/expenses/{id}")
def delete_expense(
    id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
) -> JSONResponse:
    """Get all expenses for the current user."""
    user_id = require_user_id(current_user)
    expense = session.exec(select(DBExpense).where(DBExpense.user_id == user_id, DBExpense.id == id)).first()
    if not expense:
        raise HTTPException(detail=f"Expense not found: {id}", status_code=status.HTTP_404_NOT_FOUND)
    session.delete(expense)
    session.commit()
    return JSONResponse(content={"msg": "OK"})


@app.get("/transferences", response_model=list[TransferenceRead])
def get_transferences(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[TransferenceRead]:
    """Get transferences for the current user, most recent first."""
    user_id = require_user_id(current_user)
    transferences = session.exec(
        select(DBTransference)
        .where(DBTransference.user_id == user_id)
        .order_by(DBTransference.date.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    result = []
    for t in transferences:
        category = get_global_category_by_slug(session, t.category.value)
        result.append(serialize_transference(t, category))
    return result


@app.delete("/transferences/{id}")
def delete_transference(
    id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
) -> JSONResponse:
    """Delete a transference for the current user."""
    user_id = require_user_id(current_user)
    transference = session.exec(
        select(DBTransference).where(DBTransference.user_id == user_id, DBTransference.id == id)
    ).first()
    if not transference:
        raise HTTPException(detail=f"Transference not found: {id}", status_code=status.HTTP_404_NOT_FOUND)
    session.delete(transference)
    session.commit()
    return JSONResponse(content={"msg": "OK"})


@app.post("/email/scan", status_code=status.HTTP_202_ACCEPTED)
def trigger_manual_email_scan(current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Queue an email scan manually for OAuth verification.
    Enabled only when EMAIL_SCAN_VERIFICATION_MODE=true.
    """
    if not can_use_verification_scan(current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    creds = current_user.google_credentials
    gmail_scope = "https://www.googleapis.com/auth/gmail.readonly"

    if not creds or not creds.is_valid:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Google credentials missing or invalid")

    if gmail_scope not in creds.granted_scopes():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Gmail read-only scope not granted")

    try:
        task = get_user_messages.delay(current_user.id)
    except Exception as e:
        logger.exception("Unable to queue manual scan for user %s", current_user.username)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue email scan"
        ) from e

    return JSONResponse(content={"msg": "Email scan queued", "task_id": task.id})


@app.get("/google-authorize")
def auth_google() -> RedirectResponse:
    state = google_oauth.generate_oauth_state()
    client = google_oauth.GoogleClient()
    auth_url, returned_state, code_verifier = client.authorize_oauth2(state=state)
    google_oauth.store_oauth_state(redis_client, returned_state, code_verifier)
    return RedirectResponse(auth_url)


def verify_google_id_token(raw_id_token: str | list[str] | None) -> str:
    """Verify a Google id_token and return the verified, email-verified email.

    Raises HTTPException(400) if the token is missing, fails signature/audience
    verification, the email is not verified, or the email claim is absent.
    """
    if not raw_id_token:
        raise HTTPException(status_code=400, detail="Missing id_token from Google")
    if not isinstance(raw_id_token, str):
        raise HTTPException(status_code=400, detail="Invalid id_token from Google")

    try:
        decoded = google_id_token.verify_oauth2_token(
            raw_id_token,
            google.auth.transport.requests.Request(),
            google_oauth.CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except (GoogleAuthError, ValueError) as exc:
        logger.exception("Google id_token verification failed")
        raise HTTPException(status_code=400, detail="Invalid Google token") from exc

    if decoded.get("email_verified") is not True:
        raise HTTPException(status_code=400, detail="Google email is not verified")

    email = decoded.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not present in Google token")
    return str(email)


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

    oauth_state = google_oauth.consume_oauth_state(state, redis_client) if state else None
    if not state or oauth_state is None:
        logger.debug("Invalid state: %s", state)
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    client = google_oauth.GoogleClient()
    authorization_url = str(request.url)
    try:
        credentials_dict = client.get_credentials(
            state,
            authorization_url,
            code_verifier=oauth_state.get("code_verifier"),
        )
    except OAuth2Error as exc:
        logger.exception("OAuth token exchange failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    email = verify_google_id_token(credentials_dict.get("id_token"))
    user = session.exec(select(User).where(User.email == email)).first()

    granted_scopes = credentials_dict.get("granted_scopes") or []
    gmail_granted = "https://www.googleapis.com/auth/gmail.readonly" in granted_scopes

    if not user:
        user = User(username=email, email=email)
        session.add(user)
        session.commit()
        session.refresh(user)

    save_credentials(user, credentials_dict, session)

    sub = {"sub": str(require_user_id(user))}
    access = Token.create_access_token(sub)
    refresh = Token.create_refresh_token(sub)
    # Gmail API polling is disabled by default; ingestion happens via forwarding.
    scan_status = "skipped_scope"
    if GMAIL_POLLING_ENABLED and gmail_granted:
        try:
            get_user_messages.delay(user.id)
            scan_status = "queued"
        except Exception:
            logger.exception("Unable to queue post-login scan for user %s", user.username)
            scan_status = "queue_error"

    response = RedirectResponse(f"{WEB_ADDRESS if DEBUG else ''}/dashboard?gmail_scan={scan_status}")
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
        "token": encrypt(str(credentials.get("token", ""))),
        "refresh_token": encrypt(str(credentials.get("refresh_token", ""))),
        "token_uri": str(credentials.get("token_uri", "")),
        "client_id": str(credentials.get("client_id", "")),
        "scopes_json": json.dumps(credentials.get("scopes", [])),
        "granted_scopes_json": json.dumps(credentials.get("granted_scopes", [])),
        "expiry": datetime.fromisoformat(str(credentials["expiry"])) if credentials.get("expiry") else None,
        "id_token": encrypt(str(credentials.get("id_token"))) if credentials.get("id_token") else None,
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
