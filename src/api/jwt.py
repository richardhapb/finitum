from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
import os
from fastapi.exceptions import HTTPException

from fastapi import Depends, Request, status
import jwt
from db.service import get_session
from utils.config import REFRESH_TOKEN_KEY

from db.models import User
from sqlmodel import Session, select
from jwt.exceptions import PyJWTError

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from utils.logger import get_logger


class JWTError(Exception):
    pass


logger = get_logger()

bearer_scheme = HTTPBearer()

encoded_jwt = jwt.encode({"some": "payload"}, "secret", algorithm="HS256")
jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise JWTError("Missed SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


@dataclass(frozen=True)
class Token:
    token: str
    exp: datetime

    @classmethod
    def create_refresh_token(cls, data: dict) -> "Token":
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return cls(token=encoded_jwt, exp=expire)

    @staticmethod
    def verify_refresh_token(token: str) -> dict | None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                return None
        except PyJWTError:
            return None
        else:
            return payload

    @classmethod
    async def refresh_access_token(cls, refresh_token: str, session: Session = Depends(get_session)) -> "Token":
        refresh_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

        payload = cls.verify_refresh_token(refresh_token)
        if payload is None:
            raise refresh_exception

        username: str | None = payload.get("sub")
        if username is None:
            raise refresh_exception

        user = session.exec(select(User).where(User.username == username)).first()
        if user is None:
            raise refresh_exception

        # Create new access token
        access_token_data = {"sub": user.username}
        return cls.create_access_token(access_token_data)

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: timedelta | None = None) -> "Token":
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return cls(token=encoded_jwt, exp=expire)

    @staticmethod
    def verify_token(token: str) -> dict | None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except PyJWTError:
            return None
        else:
            return payload


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    token = creds.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = Token.verify_token(token)
    if payload is None:
        # Try to refresh

        logger.debug("Access token not valid, trying with refresh token")

        refresh_token = request.cookies.get(REFRESH_TOKEN_KEY)
        if not refresh_token:
            logger.debug("Refresh token not found")
            raise credentials_exception
        token = (await Token.refresh_access_token(refresh_token, session)).token

        payload = Token.verify_token(token)
        if payload is None:
            raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        logger.debug("Username not found")
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        logger.debug("User not found")
        raise credentials_exception

    return user
