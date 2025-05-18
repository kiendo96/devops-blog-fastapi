from fastapi import (
    APIRouter, Request, Depends, Query, HTTPException, Form, status, UploadFile, File
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pathlib
from sqlmodel import Session
from typing import Optional, List
import datetime
from pydantic import EmailStr, ValidationError as PydanticValidationError
from app.api import deps
from app.crud import crud_post, crud_user, crud_comment 
from app.models.post_models import PostReadWithDetails, PostCreate as PostCreateSchema
from app.models.user_models import User, UserRead, UserCreate as UserCreateSchema 
from app.models.comment_models import CommentCreate as CommentCreateSchema
from app.core.config import settings
from app.core import security
import urllib.parse
from app.utils.file_upload import save_upload_file

APP_DIR = pathlib.Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

def get_current_year():
    return datetime.datetime.now(datetime.timezone.utc).year
templates.env.globals["settings"] = settings
templates.env.globals["get_current_year"] = get_current_year
templates.env.filters['urlencode'] = urllib.parse.quote_plus

router = APIRouter(
    tags=["Frontend Web Pages"],
)

def add_flash_message(request: Request, category: str, message: str):
    if 'flash_messages' not in request.session:
        request.session['flash_messages'] = []
    request.session['flash_messages'].append((category, message))

@router.get("/", response_class=HTMLResponse, name="home_page")
async def home_page_frontend(
    request: Request,
    page: int = Query(1, ge=1, description="Số trang, bắt đầu từ 1"),
    page_size: int = Query(6, ge=1, le=20, description="Số lượng item trên mỗi trang"),
    search: Optional[str] = Query(None, description="Từ khóa tìm kiếm trong tiêu đề hoặc nội dung bài viết"),
    tags: Optional[str] = Query(None, description="Lọc bài viết theo chuỗi tên tag, phân cách bởi dấu phẩy (VD: python,fastapi)"),
    session: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_optional_current_user)
):
    active_tags_list: Optional[List[str]] = None
    if tags:
        processed_tags = [t.strip().lower() for t in tags.split(',') if t.strip()]
        if processed_tags:
            active_tags_list = sorted(list(set(processed_tags)))

    posts_on_page, total_items = crud_post.get_db_posts(
        session=session,
        page=page,
        page_size=page_size,
        search=search,
        filter_tags=active_tags_list
    )

    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    context = {
        "request": request,
        "posts": posts_on_page,
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
        "search_query": search,
        "active_tags_string": tags,
        "active_tags_list_display": active_tags_list,
        "page_title": "Trang chủ",
        "current_user": current_user
    }
    return templates.TemplateResponse("posts/list.html", context)

@router.get("/posts/new", response_class=HTMLResponse, name="create_post_page_get")
async def create_post_page_get(
    request: Request,
    current_user: User = Depends(deps.get_current_active_user)
):
    return templates.TemplateResponse(
        "posts/create_post.html",
        {
            "request": request,
            "page_title": "Tạo Bài Viết Mới",
            "current_user": current_user,
            "form_data": {} 
        }
    )

@router.post("/posts/new", name="handle_create_post_form")
async def handle_create_post_form(
    request: Request,
    session: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    title: str = Form(...),
    content: str = Form(...),
    featured_image_file: Optional[UploadFile] = File(None),
    tags_str: Optional[str] = Form(None)
):
    tag_names_list: Optional[List[str]] = None
    if tags_str:
        tag_names_list = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]

    saved_image_path: Optional[str] = None
    form_error_message: Optional[str] = None

    if featured_image_file and featured_image_file.filename:
        saved_image_path = await save_upload_file(featured_image_file, max_size_mb=2)
        if not saved_image_path:
            form_error_message = "Upload ảnh đại diện thất bại. Ảnh phải là JPG, PNG, GIF, WEBP và nhỏ hơn 2MB."
            return templates.TemplateResponse(
                "posts/create_post.html",
                {
                    "request": request,
                    "page_title": "Tạo Bài Viết Mới",
                    "current_user": current_user,
                    "form_data": {
                        "title": title,
                        "content": content,
                        "tags_str": tags_str,
                    },
                    "error_message": form_error_message
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )

    post_in_data = {
        "title": title,
        "content": content,
        "tags": tag_names_list,
    }
    if saved_image_path:
        post_in_data["featured_image_url"] = saved_image_path 
    
    post_in = PostCreateSchema(**post_in_data)

    try:
        new_post = crud_post.create_db_post(session=session, post_in=post_in, owner_id=current_user.id)
        add_flash_message(request, "success", "Bài viết đã được tạo thành công!")
        return RedirectResponse(
            url=request.url_for('read_single_post_page', post_id=new_post.id),
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        print(f"Error creating post: {e}")
        add_flash_message(request, "danger", "Có lỗi xảy ra khi tạo bài viết. Vui lòng thử lại.")
        return templates.TemplateResponse(
            "posts/create_post.html",
            {
                "request": request,
                "page_title": "Tạo Bài Viết Mới",
                "current_user": current_user,
                "form_data": {
                    "title": title,
                    "content": content,
                    "tags_str": tags_str,
                },
                "error_message": "Có lỗi xảy ra khi tạo bài viết."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/posts/{post_id}", response_class=HTMLResponse, name="read_single_post_page")
async def read_single_post_page_frontend(
    request: Request, post_id: int,
    session: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_optional_current_user)
):
    db_post = crud_post.get_db_post(session=session, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")

    comments = crud_comment.get_db_comments_for_post(session=session, post_id=post_id, limit=50)

    login_base_url = request.url_for('login_page_get')
    redirect_target_url = str(request.url_for('read_single_post_page', post_id=post_id)) + "#comments_section"

    context = {
        "request": request, "post": db_post, "comments": comments,
        "page_title": db_post.title, "current_user": current_user,
        "login_base_url": login_base_url,
        "redirect_target_url": redirect_target_url
    }
    return templates.TemplateResponse("posts/detail.html", context)


@router.post("/posts/{post_id}/comments", name="handle_create_comment_form")
async def handle_create_comment_form(
    request: Request,
    post_id: int,
    session: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    comment_text: str = Form(..., min_length=1)
):
    db_post = crud_post.get_db_post(session=session, post_id=post_id)
    if not db_post:
        add_flash_message(request, "danger", "Bài viết không tồn tại để bình luận.")
        return RedirectResponse(url=request.url_for('home_page'), status_code=status.HTTP_302_FOUND)

    comment_in = CommentCreateSchema(text=comment_text)
    try:
        crud_comment.create_db_comment(
            session=session,
            comment_in=comment_in,
            post_id=post_id,
            owner_id=current_user.id
        )
        add_flash_message(request, "success", "Bình luận của bạn đã được gửi.")
    except Exception as e:
        print(f"Error creating comment: {e}")
        add_flash_message(request, "danger", "Có lỗi xảy ra khi gửi bình luận. Vui lòng thử lại.")

    redirect_url = str(request.url_for('read_single_post_page', post_id=post_id)) + "#comments_section"
    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_302_FOUND
    )

@router.get("/login", response_class=HTMLResponse, name="login_page_get")
async def login_page_get(
    request: Request,
    error_message: Optional[str] = Query(None),
    success_message: Optional[str] = Query(None),
    next: Optional[str] = Query(None)
):
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "page_title": "Đăng nhập",
        }
    )

@router.post("/login", name="handle_login_form")
async def handle_login_form(
    request: Request,
    session: Session = Depends(deps.get_db),
    username: str = Form(...),
    password: str = Form(...),
    next_url: Optional[str] = Query(None)
):
    user = crud_user.get_user_by_username(session, username=username)
    error_redirect_params = {}
    if next_url:
        error_redirect_params["next"] = next_url

    if not user or not security.verify_password(password, user.hashed_password): 
        error_redirect_params["error_message"] = "Tên đăng nhập hoặc mật khẩu không chính xác."
        login_url_with_error = request.url_for('login_page_get').include_query_params(**error_redirect_params)
        return RedirectResponse(url=str(login_url_with_error), status_code=status.HTTP_302_FOUND)

    if not user.is_active: 
        error_redirect_params["error_message"] = "Tài khoản của bạn chưa được kích hoạt."
        login_url_with_error = request.url_for('login_page_get').include_query_params(**error_redirect_params)
        return RedirectResponse(url=str(login_url_with_error), status_code=status.HTTP_302_FOUND)

    access_token_str = security.create_access_token(data={"sub": user.username}) 

    redirect_target_str = next_url
    if not redirect_target_str or not redirect_target_str.startswith("/"):
        redirect_target_str = request.url_for('home_page')

    response = RedirectResponse(url=str(redirect_target_str), status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token_cookie",
        value=f"Bearer {access_token_str}",
        httponly=True, samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
        path="/"
    )
    add_flash_message(request, "success", f"Chào mừng {user.username} quay trở lại!")
    return response


@router.get("/register", response_class=HTMLResponse, name="register_page_get")
async def register_page_get(
    request: Request,
    error_message: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    full_name: Optional[str] = Query(None)
):
    form_data_repopulate = {}
    if username: form_data_repopulate["username"] = username
    if email: form_data_repopulate["email"] = email
    if full_name: form_data_repopulate["full_name"] = full_name
    
    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request, 
            "page_title": "Đăng ký",
            "error_message": error_message,
            "form_data": form_data_repopulate
        }
    )

@router.post("/register", name="handle_register_form")
async def handle_register_form(
    request: Request,
    session: Session = Depends(deps.get_db),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None)
):
    form_data_to_repopulate = {
        "username": username,
        "email": email,
        "full_name": full_name
    }
    if len(password) < 8:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "page_title": "Đăng ký",
                "form_data": form_data_to_repopulate,
                "error_message": "Mật khẩu phải có ít nhất 8 ký tự."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_in_schema = UserCreateSchema(
            username=username, 
            email=email,
            password=password, 
            full_name=full_name
        )
    except PydanticValidationError as e:
        error_msg_display = "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại email."
        if e.errors() and 'type' in e.errors()[0] and 'email' in e.errors()[0]['type']:
             error_msg_display = "Địa chỉ email không hợp lệ."
        else:
            try:
                error_msg_display = e.errors()[0]['msg']
            except (IndexError, KeyError):
                pass

        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "page_title": "Đăng ký",
                "form_data": form_data_to_repopulate,
                "error_message": error_msg_display
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    db_user_by_username = crud_user.get_user_by_username(session, username=user_in_schema.username)
    if db_user_by_username:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "page_title": "Đăng ký",
                "form_data": form_data_to_repopulate,
                "error_message": "Tên đăng nhập đã tồn tại."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    db_user_by_email = crud_user.get_user_by_email(session, email=user_in_schema.email)
    if db_user_by_email:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "page_title": "Đăng ký",
                "form_data": form_data_to_repopulate,
                "error_message": "Email đã được đăng ký."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    crud_user.create_db_user(session=session, user_in=user_in_schema)

    login_url_with_success = request.url_for('login_page_get').include_query_params(success_message="Đăng ký thành công! Vui lòng đăng nhập.")
    return RedirectResponse(
        url=str(login_url_with_success),
        status_code=status.HTTP_302_FOUND
    )

@router.get("/logout", response_class=RedirectResponse, name="logout_action")
async def handle_logout(request: Request):
    add_flash_message(request, "info", "Bạn đã đăng xuất thành công.")
    response = RedirectResponse(url=request.url_for('home_page'), status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token_cookie", path="/")
    return response