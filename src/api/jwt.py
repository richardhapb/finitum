from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import Response
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase
from jwt.exceptions import PyJWTError
from sqlmodel import Session, select
from starlette.requests import Request as StRequest
from starlette.status import HTTP_403_FORBIDDEN

from db.models import User
from db.service import get_session
from utils.config import ACCESS_TOKEN_KEY, DEBUG, REFRESH_TOKEN_KEY, SECRET_KEY
from utils.logger import get_logger


class JWTError(Exception):
    pass


logger = get_logger()


class HTTPCookieBearer(HTTPBase):
    def __init__(self, *, scheme: str = "bearer", auto_error: bool = True):
        super().__init__(scheme=scheme, auto_error=auto_error)

    async def __call__(self, request: StRequest) -> HTTPAuthorizationCredentials | None:
        token = request.cookies.get(ACCESS_TOKEN_KEY)
        if not token:
            if self.auto_error:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authenticated")
            return None
        scheme = "bearer"
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=token)


bearer_scheme = HTTPCookieBearer()

if "insecure" in SECRET_KEY:
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

        sub: str | None = payload.get("sub")
        if sub is None:
            raise refresh_exception

        try:
            user_id = int(sub)
        except ValueError:
            raise refresh_exception from None

        user = session.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            raise refresh_exception

        # Create new access token
        access_token_data = {"sub": str(user.id)}
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
    response: Response,
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
        access_token = await Token.refresh_access_token(refresh_token, session)

        payload = Token.verify_token(access_token.token)
        if payload is None:
            raise credentials_exception
        set_access_cookie(response, access_token)

    sub: str | None = payload.get("sub")
    if sub is None:
        logger.debug("Subject not found")
        raise credentials_exception

    try:
        user_id = int(sub)
    except ValueError:
        logger.debug("Subject is not a valid user id")
        raise credentials_exception from None

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        logger.debug("User not found")
        raise credentials_exception

    return user


def set_refresh_cookie(response: Response, token: Token) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_KEY,
        value=token.token,
        httponly=True,
        secure=not DEBUG,  # Only send over HTTPS
        samesite="lax",  # Helps prevent CSRF attacks
        expires=token.exp,
    )


def set_access_cookie(response: Response, token: Token) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_KEY,
        value=token.token,
        httponly=True,
        secure=not DEBUG,  # Only send over HTTPS
        samesite="lax",  # Helps prevent CSRF attacks
        expires=token.exp,
    )
