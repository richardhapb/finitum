import dotenv
import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import create_db_and_tables, get_session
from sqlmodel import Session, select
from models import Expense as DBExpense, User
from fastapi.responses import RedirectResponse
from oauth import google_oauth

import utils

logger = utils.get_logger()


@asynccontextmanager
async def lifespan(app_service: FastAPI):
    """Application lifespan manager"""
    # Startup
    dotenv.load_dotenv()
    create_db_and_tables()
    logger.info("Finance manager started")
    yield

    # Shutdown
    logger.info("Finance manager shutdown")


app = FastAPI(
    title="Finance manager",
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


@app.get("/health", response_class=JSONResponse)
async def health() -> JSONResponse:
    return JSONResponse(status_code=200, content={"message": "OK"})


@app.get("/expenses")
def get_expenses(request: Request, session: Session = Depends(get_session)) -> JSONResponse | RedirectResponse:
    if "credentials" not in request.session:
        return RedirectResponse("/google-authorize")

    expenses = session.exec(select(DBExpense)).all()
    return JSONResponse(status_code=200, content={"expenses": list(expenses)})


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

    # In FastAPI, you need to manage session differently than Flask
    request.session["credentials"] = credentials
    request.session["features"] = features
    return RedirectResponse("/expenses")


def is_token_valid(token: str) -> bool:
    return token.strip("Bearer").strip() == os.getenv("JWT")


def clean_body(body: bytes) -> bytes:
    return body.replace(b"\n", b"")
