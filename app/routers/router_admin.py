from fastapi import (
    APIRouter, Depends, Request, Query, Form, HTTPException, status, UploadFile, File
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pathlib
import datetime
import urllib.parse
from typing import Optional, List

from app.api import deps
from app.models.user_models import User, UserUpdateByAdmin 
from app.models.post_models import Post, PostReadWithDetails, PostUpdateByAdmin as PostUpdateByAdminSchema
from app.models.comment_models import CommentReadWithAuthor, Comment
from app.models.tag_models import TagReadWithCount, TagUpdate as TagUpdateSchema
from app.core.config import settings
from app.crud import crud_user, crud_post, crud_comment, crud_tag
from sqlmodel import Session as SQLModelSession
from app.utils.file_upload import save_upload_file, delete_static_file

router = APIRouter(
    tags=["Admin Panel"],
    dependencies=[Depends(deps.get_current_admin_user)]
)

APP_DIR = pathlib.Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

def get_current_year():
    return datetime.datetime.now(datetime.timezone.utc).year

templates.env.globals["settings"] = settings
templates.env.globals["get_current_year"] = get_current_year

def add_flash_message(request: Request, category: str, message: str):
    if 'flash_messages' not in request.session:
        request.session['flash_messages'] = []
    request.session['flash_messages'].append((category, message))

@router.get("/", response_class=HTMLResponse, name="admin_dashboard_page")
async def admin_dashboard(
    request: Request,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user)
):
    total_users = crud_user.count_db_users(session=db)
    _, total_posts = crud_post.get_db_posts(session=db, page=1, page_size=1)
    _, total_comments = crud_comment.admin_get_db_comments(session=db, page=1, page_size=1)
    total_tags = crud_tag.count_all_db_tags(session=db)

    context = {
        "request": request,
        "page_title": "Admin Dashboard",
        "current_user": current_admin,
        "total_users": total_users,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_tags": total_tags,
    }
    return templates.TemplateResponse("admin/admin_dashboard.html", context)

@router.get("/users/", response_class=HTMLResponse, name="admin_manage_users_page")
async def admin_manage_users(
    request: Request,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None)
):
    skip = (page - 1) * page_size
    users_list = crud_user.get_db_users(session=db, skip=skip, limit=page_size, search_term=search)
    total_users_count = crud_user.count_db_users(session=db, search_term=search)

    total_pages = (total_users_count + page_size - 1) // page_size if total_users_count > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    context = {
        "request": request,
        "page_title": "Quản lý Người dùng",
        "current_user": current_admin,
        "users_list": users_list,
        "current_page_num": page,
        "current_page_size": page_size,
        "total_items": total_users_count,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
        "search_query": search,
        "base_url_name": "admin_manage_users_page",
        "query_params": request.query_params
    }
    return templates.TemplateResponse("admin/users_list.html", context)

@router.get("/users/{user_id}/edit/", response_class=HTMLResponse, name="admin_edit_user_form_page")
async def admin_edit_user_form(
    request: Request,
    user_id: int,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user)
):
    user_to_edit = crud_user.get_db_user_by_id(session=db, user_id=user_id)
    if not user_to_edit:
        add_flash_message(request, 'warning', 'Người dùng không tồn tại.')
        return RedirectResponse(url=request.url_for('admin_manage_users_page'), status_code=status.HTTP_303_SEE_OTHER)

    context = {
        "request": request,
        "page_title": f"Chỉnh sửa Người dùng: {user_to_edit.username}",
        "current_user": current_admin,
        "user_to_edit": user_to_edit,
    }
    return templates.TemplateResponse("admin/user_edit_form.html", context)

@router.post("/users/{user_id}/edit/", name="admin_handle_edit_user_form")
async def admin_handle_edit_user_form(
    request: Request,
    user_id: int,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user),
    full_name: Optional[str] = Form(None),
    is_active_form: Optional[str] = Form(None), 
    is_admin_form: Optional[str] = Form(None),  
    profile_picture_url_input: Optional[str] = Form(None),
    profile_picture_file: Optional[UploadFile] = File(None), 
    bio: Optional[str] = Form(None),
    website_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    delete_profile_picture: Optional[str] = Form(None)
):
    user_to_edit = crud_user.get_db_user_by_id(session=db, user_id=user_id)
    if not user_to_edit:
        add_flash_message(request, 'danger', 'Người dùng không tồn tại để cập nhật.')
        return RedirectResponse(url=request.url_for('admin_manage_users_page'), status_code=status.HTTP_303_SEE_OTHER)

    new_profile_picture_path: Optional[str] = user_to_edit.profile_picture_url
    
    if delete_profile_picture == "on": 
        if user_to_edit.profile_picture_url:
            await delete_static_file(user_to_edit.profile_picture_url)
        new_profile_picture_path = None
    elif profile_picture_file and profile_picture_file.filename:

        if user_to_edit.profile_picture_url:
            await delete_static_file(user_to_edit.profile_picture_url)
        
        saved_path = await save_upload_file(profile_picture_file, max_size_mb=1)
        if saved_path:
            new_profile_picture_path = saved_path
        else:
            add_flash_message(request, 'danger', 'Upload ảnh profile thất bại. Ảnh phải là JPG, PNG, GIF, WEBP và nhỏ hơn 1MB.')
            return RedirectResponse(url=request.url_for('admin_edit_user_form_page', user_id=user_id), status_code=status.HTTP_303_SEE_OTHER)
    elif profile_picture_url_input and profile_picture_url_input.strip():
        if user_to_edit.profile_picture_url and user_to_edit.profile_picture_url != profile_picture_url_input.strip():

            if user_to_edit.profile_picture_url.startswith("uploads/"):
                 await delete_static_file(user_to_edit.profile_picture_url)
        new_profile_picture_path = profile_picture_url_input.strip()
    elif profile_picture_url_input == "": 
        if user_to_edit.profile_picture_url and user_to_edit.profile_picture_url.startswith("uploads/"):
            await delete_static_file(user_to_edit.profile_picture_url)
        new_profile_picture_path = None


    update_data = {
        "full_name": full_name.strip() if full_name and full_name.strip() else None,
        "is_active": True if is_active_form == "on" else False,
        "is_admin": True if is_admin_form == "on" else False,
        "profile_picture_url": new_profile_picture_path,
        "bio": bio.strip() if bio and bio.strip() else None,
        "website_url": website_url.strip() if website_url and website_url.strip() else None,
        "linkedin_url": linkedin_url.strip() if linkedin_url and linkedin_url.strip() else None,
        "github_url": github_url.strip() if github_url and github_url.strip() else None,
    }
    
    if user_to_edit.id == current_admin.id:
        update_data["is_active"] = True
        update_data["is_admin"] = True
        if not user_to_edit.is_active : update_data["is_active"] = True 
        if not user_to_edit.is_admin : update_data["is_admin"] = True 

    user_data_to_update = UserUpdateByAdmin(
        **{k: v for k, v_list in update_data.items() for v in ([v_list] if not isinstance(v_list, list) else v_list) if v is not None or k in ["full_name", "profile_picture_url", "bio", "website_url", "linkedin_url", "github_url", "is_active", "is_admin"]}
    )

    user_data_dict_for_schema = {
        "full_name": update_data["full_name"],
        "is_active": update_data["is_active"],
        "is_admin": update_data["is_admin"],
    }
    if "profile_picture_url" in update_data: user_data_dict_for_schema["profile_picture_url"] = update_data["profile_picture_url"]
    if "bio" in update_data: user_data_dict_for_schema["bio"] = update_data["bio"]
    if "website_url" in update_data: user_data_dict_for_schema["website_url"] = update_data["website_url"]
    if "linkedin_url" in update_data: user_data_dict_for_schema["linkedin_url"] = update_data["linkedin_url"]
    if "github_url" in update_data: user_data_dict_for_schema["github_url"] = update_data["github_url"]

    user_update_in = UserUpdateByAdmin(**user_data_dict_for_schema)

    crud_user.update_user_by_admin(session=db, db_user=user_to_edit, user_in=user_update_in)
    add_flash_message(request, 'success', f"Cập nhật người dùng '{user_to_edit.username}' thành công!")

    return RedirectResponse(url=request.url_for('admin_edit_user_form_page', user_id=user_id), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/users/{user_id}/delete/", name="admin_delete_user_action")
async def admin_delete_user(
    request: Request,
    user_id: int,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user)
):
    user_to_delete = crud_user.get_db_user_by_id(session=db, user_id=user_id)

    if not user_to_delete:
        add_flash_message(request, 'warning', 'Người dùng không tồn tại.')
        return RedirectResponse(url=request.url_for('admin_manage_users_page'), status_code=status.HTTP_303_SEE_OTHER)

    if user_to_delete.id == current_admin.id:
        add_flash_message(request, 'danger', 'Bạn không thể xóa chính tài khoản của mình.')
        return RedirectResponse(url=request.url_for('admin_manage_users_page'), status_code=status.HTTP_303_SEE_OTHER)

    if user_to_delete.profile_picture_url and user_to_delete.profile_picture_url.startswith("uploads/"):
        await delete_static_file(user_to_delete.profile_picture_url)

    deleted_username = user_to_delete.username
    try:
        crud_user.delete_db_user(session=db, user_to_delete=user_to_delete)
        add_flash_message(request, 'success', f"Đã xóa thành công người dùng '{deleted_username}'.")
    except Exception as e:
        print(f"Error during user deletion: {e}")
        add_flash_message(request, 'danger', f"Có lỗi xảy ra khi xóa người dùng '{deleted_username}'. Vui lòng kiểm tra log server.")

    return RedirectResponse(url=request.url_for('admin_manage_users_page'), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/posts/", response_class=HTMLResponse, name="admin_manage_posts_page")
async def admin_manage_posts(
    request: Request,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None)
):
    posts_list, total_posts_count = crud_post.get_db_posts(
        session=db, page=page, page_size=page_size, search=search
    )

    total_pages = (total_posts_count + page_size - 1) // page_size if total_posts_count > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    context = {
        "request": request,
        "page_title": "Quản lý Bài viết",
        "current_user": current_admin,
        "posts_list": posts_list,
        "current_page_num": page,
        "current_page_size": page_size,
        "total_items": total_posts_count,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
        "search_query": search,
        "base_url_name": "admin_manage_posts_page",
        "query_params": request.query_params
    }
    return templates.TemplateResponse("admin/admin_posts_list.html", context)

@router.get("/posts/{post_id}/edit/", response_class=HTMLResponse, name="admin_edit_post_form_page")
async def admin_edit_post_form(
    request: Request,
    post_id: int,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user)
):
    post_to_edit = crud_post.get_db_post(session=db, post_id=post_id)
    if not post_to_edit:
        add_flash_message(request, 'warning', 'Bài viết không tồn tại.')
        return RedirectResponse(url=request.url_for('admin_manage_posts_page'), status_code=status.HTTP_303_SEE_OTHER)

    tags_str = ", ".join([tag.name for tag in post_to_edit.tags]) if post_to_edit.tags else ""

    context = {
        "request": request,
        "page_title": f"Chỉnh sửa Bài viết: {post_to_edit.title}",
        "current_user": current_admin,
        "post_to_edit": post_to_edit, 
        "tags_str": tags_str,
    }
    return templates.TemplateResponse("admin/admin_post_edit_form.html", context)

@router.post("/posts/{post_id}/edit/", name="admin_handle_edit_post_form")
async def admin_handle_edit_post_form(
    request: Request,
    post_id: int,
    db: SQLModelSession = Depends(deps.get_db),
    title: str = Form(...),
    content: str = Form(...),
    featured_image_file: Optional[UploadFile] = File(None),
    delete_featured_image: Optional[str] = Form(None),
    tags_str: Optional[str] = Form(None)
):
    db_post = crud_post.get_db_post(session=db, post_id=post_id)
    if not db_post:
        add_flash_message(request, 'danger', 'Bài viết không tồn tại để cập nhật.')
        return RedirectResponse(url=request.url_for('admin_manage_posts_page'), status_code=status.HTTP_303_SEE_OTHER)

    tag_names_list: Optional[List[str]] = None
    if tags_str is not None:
        tag_names_list = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]


    new_featured_image_path: Optional[str] = db_post.featured_image_url 

    if delete_featured_image == "on": 
        if db_post.featured_image_url: 
            await delete_static_file(db_post.featured_image_url) 
        new_featured_image_path = None 
    elif featured_image_file and featured_image_file.filename:
        
        if db_post.featured_image_url:
            await delete_static_file(db_post.featured_image_url)
        
        saved_path = await save_upload_file(featured_image_file, max_size_mb=2)
        if saved_path:
            new_featured_image_path = saved_path
        else:
            add_flash_message(request, 'danger', 'Upload ảnh đại diện thất bại. Ảnh phải là JPG, PNG, GIF, WEBP và nhỏ hơn 2MB.')
            
            return RedirectResponse(url=request.url_for('admin_edit_post_form_page', post_id=post_id), status_code=status.HTTP_303_SEE_OTHER)


    post_update_data = {
        "title": title,
        "content": content,
        "tags": tag_names_list,
        "featured_image_url": new_featured_image_path 
    }
    
    post_in_update = PostUpdateByAdminSchema(**post_update_data)
    
    updated_post = crud_post.admin_update_db_post(session=db, db_post=db_post, post_in=post_in_update)
    add_flash_message(request, 'success', f"Cập nhật bài viết '{updated_post.title}' thành công!")

    return RedirectResponse(url=request.url_for('admin_edit_post_form_page', post_id=updated_post.id), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/posts/{post_id}/delete/", name="admin_delete_post_action")
async def admin_delete_post(
    request: Request,
    post_id: int,
    db: SQLModelSession = Depends(deps.get_db)
):
    post_to_delete = crud_post.get_db_post(session=db, post_id=post_id)
    if not post_to_delete:
        add_flash_message(request, 'warning', 'Bài viết không tồn tại.')
        return RedirectResponse(url=request.url_for('admin_manage_posts_page'), status_code=status.HTTP_303_SEE_OTHER)

    if post_to_delete.featured_image_url and post_to_delete.featured_image_url.startswith("uploads/"):
        await delete_static_file(post_to_delete.featured_image_url)

    deleted_post_title = post_to_delete.title
    try:
        crud_post.delete_db_post(session=db, db_post=post_to_delete)
        add_flash_message(request, 'success', f"Đã xóa thành công bài viết '{deleted_post_title}' và các bình luận liên quan.")
    except Exception as e:
        print(f"Error during post deletion: {e}")
        add_flash_message(request, 'danger', f"Có lỗi xảy ra khi xóa bài viết '{deleted_post_title}'. Vui lòng kiểm tra log server.")

    return RedirectResponse(url=request.url_for('admin_manage_posts_page'), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/comments/", response_class=HTMLResponse, name="admin_manage_comments_page")
async def admin_manage_comments(
    request: Request,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None)
):
    comments_list, total_comments_count = crud_comment.admin_get_db_comments(
        session=db, page=page, page_size=page_size, search_term=search
    )

    total_pages = (total_comments_count + page_size - 1) // page_size if total_comments_count > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    context = {
        "request": request,
        "page_title": "Quản lý Bình luận",
        "current_user": current_admin,
        "comments_list": comments_list,
        "current_page_num": page,
        "current_page_size": page_size,
        "total_items": total_comments_count,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
        "search_query": search,
        "base_url_name": "admin_manage_comments_page",
        "query_params": request.query_params
    }
    return templates.TemplateResponse("admin/admin_comments_list.html", context)

@router.post("/comments/{comment_id}/delete/", name="admin_delete_comment_action")
async def admin_delete_comment(
    request: Request,
    comment_id: int,
    db: SQLModelSession = Depends(deps.get_db)
):
    comment_to_delete = crud_comment.get_db_comment(session=db, comment_id=comment_id)
    if not comment_to_delete:
        add_flash_message(request, 'warning', 'Bình luận không tồn tại.')
        return RedirectResponse(url=request.url_for('admin_manage_comments_page'), status_code=status.HTTP_303_SEE_OTHER)

    try:
        crud_comment.delete_db_comment(session=db, db_comment=comment_to_delete)
        add_flash_message(request, 'success', f"Đã xóa thành công bình luận ID {comment_id}.")
    except Exception as e:
        print(f"Error during comment deletion: {e}")
        add_flash_message(request, 'danger', f"Có lỗi xảy ra khi xóa bình luận ID {comment_id}. Vui lòng kiểm tra log server.")

    return RedirectResponse(url=request.url_for('admin_manage_comments_page'), status_code=status.HTTP_303_SEE_OTHER)


# === TAG MANAGEMENT ===
@router.get("/tags/", response_class=HTMLResponse, name="admin_manage_tags_page")
async def admin_manage_tags(
    request: Request,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None)
):
    tags_for_template, total_tags_count = crud_tag.admin_get_db_tags_with_count(
        session=db, page=page, page_size=page_size, search_term=search
    )

    total_pages = (total_tags_count + page_size - 1) // page_size if total_tags_count > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    context = {
        "request": request,
        "page_title": "Quản lý Tags",
        "current_user": current_admin,
        "tags_list": tags_for_template,
        "current_page_num": page,
        "current_page_size": page_size,
        "total_items": total_tags_count,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
        "search_query": search,
        "base_url_name": "admin_manage_tags_page",
        "query_params": request.query_params
    }
    return templates.TemplateResponse("admin/admin_tags_list.html", context)

@router.get("/tags/{tag_id}/edit/", response_class=HTMLResponse, name="admin_edit_tag_form_page")
async def admin_edit_tag_form(
    request: Request,
    tag_id: int,
    db: SQLModelSession = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_admin_user)
):
    tag_to_edit = crud_tag.get_db_tag_by_id(session=db, tag_id=tag_id)
    if not tag_to_edit:
        add_flash_message(request, 'warning', 'Tag không tồn tại.')
        return RedirectResponse(url=request.url_for('admin_manage_tags_page'), status_code=status.HTTP_303_SEE_OTHER)

    context = {
        "request": request,
        "page_title": f"Chỉnh sửa Tag: {tag_to_edit.name}",
        "current_user": current_admin,
        "tag_to_edit": tag_to_edit,
    }
    return templates.TemplateResponse("admin/admin_tag_edit_form.html", context)

@router.post("/tags/{tag_id}/edit/", name="admin_handle_edit_tag_form")
async def admin_handle_edit_tag_form(
    request: Request,
    tag_id: int,
    db: SQLModelSession = Depends(deps.get_db),
    name: str = Form(...)
):
    db_tag = crud_tag.get_db_tag_by_id(session=db, tag_id=tag_id)
    if not db_tag:
        add_flash_message(request, 'danger', 'Tag không tồn tại để cập nhật.')
        return RedirectResponse(url=request.url_for('admin_manage_tags_page'), status_code=status.HTTP_303_SEE_OTHER)

    tag_in_update = TagUpdateSchema(name=name)
    redirect_url_str = ""
    try:
        updated_tag = crud_tag.update_db_tag(session=db, db_tag=db_tag, tag_in=tag_in_update)
        if updated_tag:
            add_flash_message(request, 'success', f"Cập nhật tag '{updated_tag.name}' thành công!")
            redirect_url_str = str(request.url_for('admin_edit_tag_form_page', tag_id=updated_tag.id))
        else:
             add_flash_message(request, 'info', f"Không có thay đổi nào cho tag '{db_tag.name}'.")
             redirect_url_str = str(request.url_for('admin_edit_tag_form_page', tag_id=tag_id))

    except ValueError as e:
        add_flash_message(request, 'danger', str(e))
        redirect_url_str = str(request.url_for('admin_edit_tag_form_page', tag_id=tag_id))

    return RedirectResponse(url=redirect_url_str, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tags/{tag_id}/delete/", name="admin_delete_tag_action")
async def admin_delete_tag(
    request: Request,
    tag_id: int,
    db: SQLModelSession = Depends(deps.get_db)
):
    tag_to_delete = crud_tag.get_db_tag_by_id(session=db, tag_id=tag_id)
    if not tag_to_delete:
        add_flash_message(request, 'warning', 'Tag không tồn tại.')
        return RedirectResponse(url=request.url_for('admin_manage_tags_page'), status_code=status.HTTP_303_SEE_OTHER)

    deleted_tag_name = tag_to_delete.name
    try:
        crud_tag.delete_db_tag(session=db, db_tag=tag_to_delete)
        add_flash_message(request, 'success', f"Đã xóa thành công tag '{deleted_tag_name}'.")
    except Exception as e:
        print(f"Error during tag deletion: {e}")
        add_flash_message(request, 'danger', f"Có lỗi xảy ra khi xóa tag '{deleted_tag_name}'. Vui lòng kiểm tra log server.")

    return RedirectResponse(url=request.url_for('admin_manage_tags_page'), status_code=status.HTTP_303_SEE_OTHER)