from typing import List, TypeVar, Generic, Optional
from pydantic import BaseModel, Field

ItemType = TypeVar('ItemType')

class Page(BaseModel, Generic[ItemType]):
    items: list[ItemType]
    total_items: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool
    search_query: Optional[str] = None
    active_tags: Optional[List[str]] = None
    
    class Config:
        from_attributes = True