from sqlmodel import Field, SQLModel, Relationship
from pydantic import EmailStr, field_validator
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .post_models import Post
    from .comment_models import Comment

class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=50)
    email: EmailStr = Field(unique=True, index=True)
    full_name: Optional[str] = Field(default=None, max_length=100)
    
    profile_picture_url: Optional[str] = Field(default=None, description="URL to user's profile picture")
    bio: Optional[str] = Field(default=None, max_length=300, description="A short biography of the user")
    website_url: Optional[str] = Field(default=None, description="User's personal website URL")
    linkedin_url: Optional[str] = Field(default=None, description="User's LinkedIn profile URL")
    github_url: Optional[str] = Field(default=None, description="User's GitHub profile URL")

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    
    posts: List["Post"] = Relationship(back_populates="owner")
    comments: list['Comment'] = Relationship(back_populates='owner')
    
class UserRead(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    
class UserUpdateByAdmin(SQLModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    
    profile_picture_url: Optional[str] = None 
    bio: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None