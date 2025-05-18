from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud import crud_user

class Token(BaseModel):
    access_token: str
    token_type: str

router = APIRouter()

@router.post('/token', response_model=Token)
async def login_for_access_token(
    session: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    print(f"Attempting login for username: {form_data.username}")
    print(f"Password received (plain): {form_data.password}")
    user = crud_user.get_user_by_username(session, username=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}