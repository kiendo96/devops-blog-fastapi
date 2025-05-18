from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.api import deps
from app.crud import crud_tag
from app.models.tag_models import TagCreate, TagRead, Tag
from app.models.user_models import User

router = APIRouter()

@router.post("/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    *,
    tag_in: TagCreate,
    session: Session = Depends(deps.get_db),
):
    try:
        tag = crud_tag.create_db_tag(session=session, tag_in=tag_in)
    except ValueError as e:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return tag

@router.get("/", response_model=List[TagRead])
async def list_all_tags(
    *,
    session: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
):

    tags = crud_tag.get_db_tags(session=session, skip=skip, limit=limit)
    return tags