from sqlmodel import Field, SQLModel, Relationship
import datetime
from typing import Optional, TYPE_CHECKING
from .user_models import UserRead

if TYPE_CHECKING:
    from .user_models import User
    from .post_models import Post
    
class CommentBase(SQLModel):
    text: str = Field(min_length=1, max_length=500)

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    post_id: int = Field(foreign_key="post.id", index=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    post: "Post" = Relationship(back_populates="comments")
    owner: "User" = Relationship(back_populates="comments")
    
class CommentRead(CommentBase):
    id: int
    created_at: datetime.datetime
    post_id: int
    owner_id: int

class CommentReadWithAuthor(CommentRead):
    owner: Optional["UserRead"] = None 