import asyncio
import sys
import os
from getpass import getpass


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from sqlmodel import Session
from app.db.session import engine
from app.models.user_models import User, UserCreate
from app.core.security import get_password_hash
from app.crud import crud_user

def create_admin_user_sync():

    print("--- Tạo tài khoản Admin ---")
    
    while True:
        username = input("Nhập tên đăng nhập cho admin: ").strip()
        if username:
            break
        print("Tên đăng nhập không được để trống.")

    while True:
        email = input("Nhập email cho admin: ").strip()
        if email and "@" in email:
            break
        print("Email không hợp lệ.")

    while True:
        password = getpass("Nhập mật khẩu cho admin (ít nhất 8 ký tự): ")
        if len(password) >= 8:
            password_confirmation = getpass("Xác nhận mật khẩu: ")
            if password == password_confirmation:
                break
            else:
                print("Mật khẩu không khớp. Vui lòng thử lại.")
        else:
            print("Mật khẩu phải có ít nhất 8 ký tự.")

    full_name = input("Nhập tên đầy đủ (tùy chọn, có thể bỏ trống): ").strip() or None

    with Session(engine) as session:
        db_user_by_username = crud_user.get_user_by_username(session, username=username)
        if db_user_by_username:
            print(f"Lỗi: Tên đăng nhập '{username}' đã tồn tại.")
            return

        db_user_by_email = crud_user.get_user_by_email(session, email=email)
        if db_user_by_email:
            print(f"Lỗi: Email '{email}' đã được đăng ký.")
            return

        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_admin=True
        )
        
        try:
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            print(f"Tạo tài khoản admin '{admin_user.username}' thành công!")
        except Exception as e:
            session.rollback()
            print(f"Lỗi khi tạo tài khoản admin: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    db_path_check = os.path.join(PROJECT_ROOT, "data", "blog.db") 
    if not os.path.exists(db_path_check):
        print(f"LƯU Ý: File database tại '{db_path_check}' không tìm thấy.")
        print("Nếu bạn chưa chạy Alembic migrations, hãy chạy 'alembic upgrade head' trước.")
        print("Nếu bạn đang dùng Docker, hãy đảm bảo đường dẫn database là chính xác hoặc chạy script này bên trong container có mount volume DB.")
    
    create_admin_user_sync()
