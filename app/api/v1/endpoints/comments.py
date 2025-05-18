from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.api import deps
from app.crud import crud_comment, crud_post
from app.models.comment_models import CommentCreate, CommentRead, CommentReadWithAuthor
from app.models.user_models import User


router = APIRouter()

@router.post("/posts/{post_id}/comments/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment_for_post(
    *,
    post_id: int,
    comment_in: CommentCreate,
    session: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    post = crud_post.get_db_post(session=session, post_id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",
        )

    comment = crud_comment.create_db_comment(
        session=session,
        comment_in=comment_in,
        post_id=post_id,
        owner_id=current_user.id
    )

    return comment

@router.get("/posts/{post_id}/comments/", response_model=List[CommentReadWithAuthor])
async def list_comments_for_post(
    *,
    post_id: int,
    session: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 20
):
    post = crud_post.get_db_post(session=session, post_id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found.",
        )

    comments_from_db = crud_comment.get_db_comments_for_post(
        session=session, post_id=post_id, skip=skip, limit=limit
    )
    return comments_from_db

@router.delete("/comments/{comment_id}", status_code=status.HTTP_200_OK, name="delete_comment_api")
async def delete_comment_api(
    *,
    comment_id: int,
    session: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    db_comment = crud_comment.get_db_comment(session=session, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found.",
        )

    if db_comment.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permission to delete this comment."
        )

    crud_comment.delete_db_comment(session=session, db_comment=db_comment)
    return {"message": f"Comment with id {comment_id} deleted successfully."}