import dotenv
import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import utils

logger = utils.get_logger()

@asynccontextmanager
async def lifespan(app_service: FastAPI):
    """Application lifespan manager"""
    # Startup
    dotenv.load_dotenv()
    logger.info("Finance manager started")
    yield

    # Shutdown
    logger.info("Finance manager shutdown")


app = FastAPI(
    title="Finance manager",
    description="Handle the expenses and manage finance elements",
    version="1.0.0",
    lifespan=lifespan
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

@app.post("/expense", response_class=JSONResponse)
async def new_expense(request: Request) -> JSONResponse:
    headers = request.headers
    token = headers.get("Authorization", "")

    if token.strip("Bearer").strip() != os.getenv("JWT"):
        return JSONResponse(status_code=403, content={"message": "Unauthorized" })

    data = clean_body(await request.body())
    try:
        deserialized = json.loads(data)
    except json.JSONDecodeError as e:
        logger.error("Error deserializing json: %s", e)
        return JSONResponse(status_code=400, content={"message": "Unable to deserialize JSON"})
    print(f"Received: {deserialized}")

    return JSONResponse(status_code=200, content={"message": "OK"})

def clean_body(body: bytes) -> bytes:
    return body.replace(b'\n', b'')

