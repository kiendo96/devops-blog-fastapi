from typing import List, Optional, Tuple
from sqlmodel import Session, select, func, col

from app.models.tag_models import Tag, TagCreate, TagUpdate, TagReadWithCount
from app.models.link_models import PostTagLink

def get_db_tag_by_name(session: Session, *, name: str) -> Optional[Tag]:
    statement = select(Tag).where(func.lower(Tag.name) == name.lower())
    return session.exec(statement).first()

def get_db_tag_by_id(session: Session, *, tag_id: int) -> Optional[Tag]:
    return session.get(Tag, tag_id)

def create_db_tag(session: Session, *, tag_in: TagCreate) -> Tag:
    normalized_name = tag_in.name.lower().strip()
    if not normalized_name:
        raise ValueError("Tên tag không được để trống")

    db_tag = get_db_tag_by_name(session, name=normalized_name)
    if db_tag:
        return db_tag

    tag_data_for_create = TagCreate(name=normalized_name)
    db_tag_obj = Tag.model_validate(tag_data_for_create)

    session.add(db_tag_obj)
    session.commit()
    session.refresh(db_tag_obj)
    return db_tag_obj

def get_db_tags(
    session: Session, *, 
    skip: int = 0, 
    limit: int = 100
) -> List[Tag]:
    statement = select(Tag).offset(skip).limit(limit).order_by(Tag.name)
    tags = session.exec(statement).all()
    return tags

def admin_get_db_tags_with_count(
    session: Session, *,
    page: int,
    page_size: int,
    search_term: Optional[str] = None
) -> Tuple[List[TagReadWithCount], int]:
    offset = (page - 1) * page_size

    post_count_subquery = (
        select(PostTagLink.tag_id, func.count(PostTagLink.post_id).label("posts_count"))
        .group_by(PostTagLink.tag_id)
        .subquery()
    )

    statement_items = (
        select(
            Tag,
            func.coalesce(post_count_subquery.c.posts_count, 0).label("calculated_posts_count")
        )
        .outerjoin(post_count_subquery, Tag.id == post_count_subquery.c.tag_id)
    )
    
    count_statement = select(func.count(Tag.id))

    if search_term:
        search_pattern = f"%{search_term.lower()}%"
        statement_items = statement_items.where(Tag.name.ilike(search_pattern))
        count_statement = count_statement.where(Tag.name.ilike(search_pattern))

    statement_items = statement_items.order_by(Tag.name).offset(offset).limit(page_size)
    
    results_from_db = session.exec(statement_items).all()
    
    tags_with_count: List[TagReadWithCount] = []
    for tag_obj, p_count in results_from_db:
        tags_with_count.append(
            TagReadWithCount(id=tag_obj.id, name=tag_obj.name, posts_count=p_count)
        )
        
    total_items = session.exec(count_statement).one_or_none() or 0
    
    return tags_with_count, total_items


def count_all_db_tags(session: Session, search_term: Optional[str] = None) -> int:
    statement = select(func.count(Tag.id))
    if search_term:
        search_pattern = f"%{search_term.lower()}%"
        statement = statement.where(Tag.name.ilike(search_pattern))
    count = session.exec(statement).one_or_none()
    return count if count is not None else 0

def update_db_tag(session: Session, *, db_tag: Tag, tag_in: TagUpdate) -> Optional[Tag]:
    if tag_in.name is None:
        return db_tag

    new_name_normalized = tag_in.name.lower().strip()
    if not new_name_normalized:
        raise ValueError("Tên tag mới không được để trống.")
    
    if new_name_normalized == db_tag.name.lower():
        return db_tag

    existing_tag_with_new_name = get_db_tag_by_name(session, name=new_name_normalized)
    if existing_tag_with_new_name and existing_tag_with_new_name.id != db_tag.id:
        raise ValueError(f"Tên tag '{new_name_normalized}' đã tồn tại.")

    db_tag.name = new_name_normalized
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag

def delete_db_tag(session: Session, *, db_tag: Tag) -> bool:
    delete_links_statement = PostTagLink.__table__.delete().where(PostTagLink.tag_id == db_tag.id)
    session.exec(delete_links_statement)

    session.delete(db_tag)
    session.commit()
    return True