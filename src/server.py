import dotenv
import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import create_db_and_tables, get_session
from sqlmodel import Session, select
from models import Expense as DBExpense

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
def get_expenses(request: Request, session: Session = Depends(get_session)) -> JSONResponse:
    headers = request.headers
    token = headers.get("Authorization", "")

    if not is_token_valid(token):
        return JSONResponse(status_code=403, content={"message": "Unauthorized"})

    expenses = session.exec(select(DBExpense)).all()
    return JSONResponse(status_code=200, content={"expenses": list(expenses)})


def is_token_valid(token: str) -> bool:
    return token.strip("Bearer").strip() == os.getenv("JWT")


def clean_body(body: bytes) -> bytes:
    return body.replace(b"\n", b"")
