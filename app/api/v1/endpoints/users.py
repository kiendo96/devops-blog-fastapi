from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional

from app.api import deps
from app.crud import crud_user
from app.models.user_models import User, UserCreate, UserBase, UserRead

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, name="register_new_user_api")
async def register_new_user(
    *,
    session: Session = Depends(deps.get_db),
    user_in: UserCreate
):
    """
    Create new user
    Username and Email is only one
    """
    db_user_by_username = crud_user.get_user_by_username(session, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered."
        )
    
    db_user_by_email = crud_user.get_user_by_email(session, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )
    
    user = crud_user.create_db_user(session=session, user_in=user_in)
    return user

@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    return current_user