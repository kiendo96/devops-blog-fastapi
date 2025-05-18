from sqlmodel import Field, SQLModel, Relationship
import datetime
from typing import Optional, TYPE_CHECKING, List
from .link_models import PostTagLink
from .tag_models import Tag, TagRead

if TYPE_CHECKING:
    from .user_models import User, UserRead
    from .comment_models import Comment, CommentRead


class PostBase(SQLModel):
    title: str
    content: str
    featured_image_url: Optional[str] = Field(default=None)

class PostCreate(PostBase):
    tags: Optional[List[str]] = None

class PostUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    featured_image_url: Optional[str] = Field(default=None)

class PostUpdateByAdmin(PostUpdate):
    tags: Optional[List[str]] = None

class Post(PostBase, table=True):
    id: Optional[int] = Field(unique=True, primary_key=True, index=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    owner: Optional["User"] = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(back_populates="post")
    tags: List["Tag"] = Relationship(back_populates="posts", link_model=PostTagLink)

class PostRead(PostBase):
    id: int
    created_at: datetime.datetime
    owner_id: Optional[int] = None

class PostReadWithDetails(PostRead):
    owner: Optional["UserRead"] = None
    comments: List["CommentRead"] = []
    tags: List[TagRead] = []