from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List, Optional

from app.crud import crud_post
from app.models import post_models, user_models
from app.api import deps
from app.models.pagination import Page
from app.models.post_models import Post, PostCreate, PostUpdate, PostRead, PostReadWithDetails
from app.models.tag_models import TagRead

router = APIRouter()

@router.post("/", response_model=PostReadWithDetails, status_code=201)
def create_post_endpoint(
    *,
    session: Session = Depends(deps.get_db),
    post_in: post_models.PostCreate,
    current_user: user_models.User = Depends(deps.get_current_active_user)
):
    post = crud_post.create_db_post(
        session=session, 
        post_in=post_in,
        owner_id=current_user.id
    )
    return post

@router.get("/", response_model=Page[PostReadWithDetails])
def read_posts_endpoint(
    *,
    page: int = Query(1, ge=1, description="So trang, bat dau tu 1"),
    page_size: int = Query(20, ge=1, le=100, description="So luong item tren moi trang"),
    search: Optional[str] = Query(None, description="Tu khoa tim kiem trong title or content of post"),
    tags: Optional[List[str]] = Query(None, description="Lọc bài viết theo danh sách tên tag (phân cách bằng nhiều tham số tags=tag1&tags=tag2)"),
    session: Session = Depends(deps.get_db)
):
    posts_on_page, total_items = crud_post.get_db_posts(
        session=session, page=page, page_size=page_size, search=search, filter_tags=tags
    )
    
    if total_items == 0:
        total_pages = 0
    else:
        total_pages = (total_items + page_size - 1) // page_size
        
    has_next = page < total_pages
    has_previous = page > 1

    return Page[PostReadWithDetails](
        items=posts_on_page,
        total_items=total_items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
        search_query=search,
        active_tags=tags
    )

@router.put("/{post_id}", response_model=post_models.PostRead)
def update_post_endpoint(
    post_id: int,
    *,
    session: Session = Depends(deps.get_db),
    post_in: post_models.PostUpdate,
    current_user: user_models.User = Depends(deps.get_current_active_user)
):
    db_post = crud_post.get_db_post(session=session, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail=f"Post not found")
    if db_post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permission")
    update_post = crud_post.update_db_post(session=session, db_post=db_post, post_in=post_in)
    return update_post

@router.delete("/{post_id}", status_code=200)
def delete_post_endpoint(
    post_id: int,
    *,
    session: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user)
):
    db_post  = crud_post.get_db_post(session=session, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permission")
    crud_post.delete_db_post(session=session, db_post=db_post)
    return {"message": f"Post with id {post_id} has been deleted successfully"}

@router.get("/{post_id}", response_model=PostReadWithDetails)
def read_single_post_endpoint(
    post_id: int,
    session: Session = Depends(deps.get_db)
):
    db_post = crud_post.get_db_post(session=session, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail=f"Post with id {post_id} not found")
    return db_post