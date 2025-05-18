from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlmodel import Session

from app.db.session import get_session_local
from app.core import security
from app.core.config import settings
from app.models.user_models import User
from app.crud import crud_user


def get_db() -> Generator[Session, None, None]:
    yield from get_session_local()

async def get_token_data(
    request: Request,
    token_from_cookie: Optional[str] = Cookie(None, alias="access_token_cookie"),
    token_from_header: Optional[str] = Depends(security.cookie_oauth2_scheme)
) -> Optional[str]:
    if token_from_cookie:
        if token_from_cookie.startswith("Bearer "):
            return token_from_cookie.split("Bearer ")[1]
        return token_from_cookie
    if token_from_header:
        return token_from_header
    return None

async def get_optional_current_user(
    session: Session = Depends(get_db),
    token_str: Optional[str] = Depends(get_token_data)
) -> Optional[User]:
    if not token_str:
        return None

    username = security.decode_access_token(token=token_str)
    if username is None:
        return None

    user = crud_user.get_user_by_username(session=session, username=username)
    return user

async def get_current_user(
    current_user_optional: Optional[User] = Depends(get_optional_current_user)
) -> User:
    if current_user_optional is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user_optional

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập vào khu vực này."
        )
    return current_user