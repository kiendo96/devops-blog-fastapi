from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
import pathlib
from starlette.middleware.sessions import SessionMiddleware

from app.routers.router_api_v1 import api_v1_router
from app.routers.router_pages import router as pages_router
from app.routers.router_admin import router as admin_router
from app.core.config import settings

APP_ROOT_DIR = pathlib.Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    print("Lifespan event: Startup - Database schema managed by Alembic.")
    yield
    print("Lifespan event: Shutdown")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware, secret_key=settings.SECRET_KEY
)

app.mount(
    "/static",
    StaticFiles(directory=str(APP_ROOT_DIR / "static")),
    name="static"
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)
app.include_router(pages_router)
app.include_router(
    admin_router,
    prefix="/admin",
)

@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def root_redirect(request: Request):
    try:
        home_url = request.url_for('home_page')
        return RedirectResponse(url=home_url)
    except Exception as e:
        print(f"Error generating root redirect URL: {e}")
        return RedirectResponse(url="/")