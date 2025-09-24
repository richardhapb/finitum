from datetime import datetime, timedelta, timezone
import os
from fastapi.exceptions import HTTPException

from fastapi import Depends, status
import jwt
from db.service import get_session

from db.models import Token, User
from sqlmodel import Session, select
from jwt.exceptions import PyJWTError

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin")

encoded_jwt = jwt.encode({"some": "payload"}, "secret", algorithm="HS256")
jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])

# Store these in environment variables in production
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise Exception("Missed SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_refresh_token(data: dict) -> Token:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return Token(token=encoded_jwt, exp=expire)


def verify_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except PyJWTError:
        return None


async def refresh_access_token(refresh_token: str, session: Session = Depends(get_session)) -> Token:
    refresh_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_refresh_token(refresh_token)
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
    return create_access_token(access_token_data)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> Token:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return Token(token=encoded_jwt, exp=expire)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception

    return user
