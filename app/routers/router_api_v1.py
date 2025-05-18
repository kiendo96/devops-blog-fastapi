from fastapi import APIRouter

from app.api.v1.endpoints import login, users, posts, comments, tags

api_v1_router = APIRouter()
api_v1_router.include_router(login.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
api_v1_router.include_router(comments.router, tags=["Comments"])
api_v1_router.include_router(tags.router, prefix="/tags", tags=["Tags"])