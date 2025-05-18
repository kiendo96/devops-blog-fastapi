from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

from .link_models import PostTagLink 

if TYPE_CHECKING:
    from .post_models import Post

class TagBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=100)

class TagCreate(TagBase):
    pass

class TagUpdate(SQLModel):
    name: Optional[str] = None

class TagRead(TagBase):
    id: int
    
class TagReadWithCount(TagRead):
    posts_count: int = 0

class Tag(TagBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    
    posts: List["Post"] = Relationship(
        back_populates="tags", 
        link_model=PostTagLink
    )