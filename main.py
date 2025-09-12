import bs4
import dotenv
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("fin-make")


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
    description="Handle the outcomes and manage finance elements",
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

@app.post("/outcome", response_class=JSONResponse)
async def new_outcome(request: Request) -> JSONResponse:
    data = await request.json()
    headers = request.headers
    token = headers.get("Authorization", "")
    if token.strip() != os.getenv("JSW_TOKEN"):
        return JSONResponse(status_code=403, content={"message", "Unauthorized" })
    print(f"Received: {data}")

    return JSONResponse(status_code=200, content={"message": "OK"})


