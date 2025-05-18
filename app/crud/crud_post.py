from sqlmodel import Session, select, func, or_, distinct
from typing import Optional, List, Tuple

from app.models.post_models import Post, PostCreate, PostUpdate, PostUpdateByAdmin
from app.models.tag_models import Tag, TagCreate
from app.models.link_models import PostTagLink
from . import crud_tag

def create_db_post(
    session: Session, *,
    post_in: PostCreate,
    owner_id: int
) -> Post:
    post_data = post_in.model_dump(exclude={"tags"})
    db_post = Post(**post_data, owner_id=owner_id)

    if post_in.tags:
        db_post.tags.clear()
        for tag_name in post_in.tags:
            if tag_name.strip():
                tag_obj = crud_tag.create_db_tag(session=session, tag_in=TagCreate(name=tag_name))
                if tag_obj not in db_post.tags:
                    db_post.tags.append(tag_obj)
    
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post

def get_db_post(session: Session, post_id: int) -> Optional[Post]:
    return session.get(Post, post_id)

def get_db_posts(
    session: Session,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    filter_tags: Optional[List[str]] = None,
    author_id: Optional[int] = None
) -> Tuple[List[Post], int]:
    offset = (page - 1) * page_size
    
    statement_items = select(Post)
    count_statement = select(func.count(Post.id)).select_from(Post)
    
    conditions = []
    if search:
        search_term = f"%{search.lower()}%"
        conditions.append(or_(
            Post.title.ilike(search_term),
            Post.content.ilike(search_term)
        ))
    
    if author_id is not None:
        conditions.append(Post.owner_id == author_id)

    if conditions:
        for condition in conditions:
            statement_items = statement_items.where(condition)
            count_statement = count_statement.where(condition)
            
    if filter_tags and len(filter_tags) > 0:
        normalized_filter_tags = [tag.lower().strip() for tag in filter_tags if tag.strip()]
        if normalized_filter_tags:
            tag_filter_condition = Tag.name.in_(normalized_filter_tags)
            
            statement_items = (
                statement_items.distinct()
                .join(PostTagLink, Post.id == PostTagLink.post_id)
                .join(Tag, PostTagLink.tag_id == Tag.id)
                .where(tag_filter_condition)
            )

            subquery_for_count = (
                select(distinct(Post.id))
                .join(PostTagLink, Post.id == PostTagLink.post_id)
                .join(Tag, PostTagLink.tag_id == Tag.id)
                .where(tag_filter_condition)
            )
            if conditions:
                for condition in conditions:
                    subquery_for_count = subquery_for_count.where(condition)
            
            count_statement = select(func.count()).select_from(subquery_for_count.alias("subquery_for_count"))


    statement_items = statement_items.order_by(Post.created_at.desc()).offset(offset).limit(page_size)
    
    posts_on_page = session.exec(statement_items).all()
    total_items = session.exec(count_statement).one_or_none() or 0
    
    return posts_on_page, total_items


def update_db_post(
    session: Session, *, db_post: Post, post_in: PostUpdate
) -> Post:
    update_data = post_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post


def admin_update_db_post(
    session: Session, *, db_post: Post, post_in: PostUpdateByAdmin
) -> Post:
    update_data = post_in.model_dump(exclude={"tags"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)

    if post_in.tags is not None:
        db_post.tags.clear()
        for tag_name in post_in.tags:
            if tag_name.strip():
                tag_obj = crud_tag.create_db_tag(session=session, tag_in=TagCreate(name=tag_name))
                if tag_obj not in db_post.tags:
                    db_post.tags.append(tag_obj)
    
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post


def delete_db_post(session: Session, *, db_post: Post) -> None:
    from . import crud_comment
    related_comments = crud_comment.get_db_comments_for_post(session=session, post_id=db_post.id, limit=1000)
    for comment in related_comments:
        session.delete(comment)
    
    session.delete(db_post)
    session.commit()


def unset_posts_owner(session: Session, *, owner_id: int) -> None:
    statement = select(Post).where(Post.owner_id == owner_id)
    posts_to_update = session.exec(statement).all()
    
    if not posts_to_update:
        return

    for post in posts_to_update:
        post.owner_id = None
        session.add(post)
