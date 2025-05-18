from sqlmodel import Session, select, func, or_
from typing import Optional
from app.models.user_models import User, UserCreate, UserUpdateByAdmin
from app.core.security import get_password_hash
from . import crud_post
from . import crud_comment

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def create_db_user(session: Session, user_in: UserCreate) -> User:
    user_data = user_in.model_dump(exclude={"password"})
    hashed_password = get_password_hash(user_in.password)
    db_user = User(**user_data, hashed_password=hashed_password)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_db_user_by_id(session: Session, user_id: int) -> Optional[User]:
    user = session.get(User, user_id)
    return user

def get_db_users(
    session: Session, *, skip: int = 0, limit: int = 100, search_term: Optional[str] = None
) -> list[User]:
    statement = select(User)
    if search_term:
        search_pattern = f"%{search_term}%"
        statement = statement.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    statement = statement.offset(skip).limit(limit).order_by(User.id)
    users = session.exec(statement).all()
    return users

def update_user_by_admin(
    session: Session, *, db_user: User, user_in: UserUpdateByAdmin
) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def count_db_users(
    session: Session, *,
    search_term: Optional[str] = None
) -> int:
    statement = select(func.count(User.id))
    if search_term:
        search_pattern = f"%{search_term}%"
        statement = statement.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    count = session.exec(statement).one_or_none()
    return count if count is not None else 0

def delete_db_user(session: Session, *, user_to_delete: User) -> bool:
    if not user_to_delete:
        return False

    user_id_to_delete = user_to_delete.id

    try:
        crud_post.unset_posts_owner(session=session, owner_id=user_id_to_delete)
        crud_comment.delete_db_comments_by_owner(session=session, owner_id=user_id_to_delete)
        session.delete(user_to_delete)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error deleting user {user_to_delete.username}: {e}")
        raise e