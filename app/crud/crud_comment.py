from typing import List, Optional, Tuple
from sqlmodel import Session, select, func, or_

from app.models.comment_models import Comment, CommentCreate
from app.models.post_models import Post
from app.models.user_models import User

def create_db_comment(
    session: Session, *,
    comment_in: CommentCreate,
    post_id: int,
    owner_id: int
) -> Comment:
    comment_data = comment_in.model_dump()
    db_comment = Comment(**comment_data, post_id=post_id, owner_id=owner_id)
    
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment

def get_db_comments_for_post(
    session: Session, *,
    post_id: int,
    skip: int = 0,
    limit: int = 20
) -> List[Comment]:
    statement = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
        .offset(skip).limit(limit)
    )
    comments = session.exec(statement).all()
    return comments

def get_db_comment(session: Session, *, comment_id: int) -> Optional[Comment]:
    return session.get(Comment, comment_id)

def delete_db_comment(session: Session, *, db_comment: Comment) -> None:
    session.delete(db_comment)
    session.commit()


def admin_get_db_comments(
    session: Session, *,
    page: int,
    page_size: int,
    search_term: Optional[str] = None,
    author_id: Optional[int] = None,
    post_id_filter: Optional[int] = None
) -> Tuple[List[Comment], int]:
    offset = (page - 1) * page_size
    
    statement_items = select(Comment)
    count_statement = select(func.count(Comment.id)).select_from(Comment)
    
    conditions = []
    if search_term:
        search_pattern = f"%{search_term.lower()}%"
        conditions.append(Comment.text.ilike(search_pattern))


    if author_id is not None:
        conditions.append(Comment.owner_id == author_id)
    
    if post_id_filter is not None:
        conditions.append(Comment.post_id == post_id_filter)

    if conditions:
        for condition in conditions:
            statement_items = statement_items.where(condition)
            count_statement = count_statement.where(condition)


    statement_items = statement_items.order_by(Comment.created_at.desc()).offset(offset).limit(page_size)
    
    comments_on_page = session.exec(statement_items).all()
    total_items = session.exec(count_statement).one_or_none() or 0
    
    return comments_on_page, total_items

def delete_db_comments_by_owner(session: Session, *, owner_id: int) -> int:
    statement = select(Comment).where(Comment.owner_id == owner_id)
    comments_to_delete = session.exec(statement).all()
    
    num_deleted = 0
    if not comments_to_delete:
        return num_deleted

    for comment in comments_to_delete:
        session.delete(comment)
        num_deleted += 1
    return num_deleted