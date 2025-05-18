from typing import Optional
from sqlmodel import Field, SQLModel

class PostTagLink(SQLModel, table=True):
    post_id: Optional[int] = Field(default=None, primary_key=True, foreign_key="post.id")
    tag_id: Optional[int] = Field(default=None, primary_key=True, foreign_key="tag.id")