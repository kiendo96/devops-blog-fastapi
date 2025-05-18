import pathlib
import shutil
import uuid
from fastapi import UploadFile
from typing import Optional

# Đường dẫn gốc của ứng dụng (thư mục chứa thư mục 'app')
# Giả sử file này nằm trong app/utils/file_upload.py
# APP_ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
# Hoặc bạn có thể định nghĩa rõ ràng hơn nếu cấu trúc khác
# Để đơn giản, chúng ta sẽ giả định APP_ROOT_DIR được truyền vào hoặc lấy từ config
# Tuy nhiên, trong ví dụ này, chúng ta sẽ xây dựng đường dẫn từ vị trí của file main.py hoặc config

# Định nghĩa đường dẫn tĩnh cơ sở
# Giả sử file này nằm trong app/utils, thư mục static nằm cùng cấp với app (nếu main.py ở ngoài app)
# Hoặc nếu main.py trong app, thì static cũng trong app.
# Dựa trên cấu trúc của bạn, APP_ROOT_DIR là thư mục 'app'
APP_ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent # trỏ đến thư mục 'app'
STATIC_DIR = APP_ROOT_DIR / "static"
UPLOAD_DIR_IMAGES = STATIC_DIR / "uploads" / "images"

# Tạo thư mục nếu chưa tồn tại
UPLOAD_DIR_IMAGES.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def get_file_extension(filename: str) -> Optional[str]:
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None

async def save_upload_file(
    upload_file: UploadFile,
    destination_dir: pathlib.Path = UPLOAD_DIR_IMAGES,
    max_size_mb: Optional[float] = 5  # Giới hạn kích thước file là 5MB
) -> Optional[str]:
    """
    Lưu file được upload, kiểm tra extension và kích thước.
    Trả về đường dẫn tương đối (tính từ thư mục static) nếu thành công, None nếu thất bại.
    """
    if not upload_file.filename:
        return None

    extension = get_file_extension(upload_file.filename)
    if not extension or extension not in ALLOWED_EXTENSIONS:
        # Có thể raise HTTPException ở đây hoặc trả về None để route handler xử lý
        print(f"File extension not allowed: {extension}")
        return None

    # Kiểm tra kích thước file (xấp xỉ)
    if max_size_mb:
        # Đọc nội dung file để kiểm tra kích thước chính xác hơn
        # upload_file.file.seek(0, 2) # Di chuyển con trỏ đến cuối file
        # file_size = upload_file.file.tell() # Lấy vị trí hiện tại (kích thước)
        # upload_file.file.seek(0) # Đưa con trỏ về đầu file để đọc sau này
        # if file_size > max_size_mb * 1024 * 1024:
        #     print(f"File too large: {file_size / (1024*1024):.2f}MB")
        #     return None
        # Cách đơn giản hơn, dựa vào content_length nếu có, nhưng không hoàn toàn đáng tin cậy
        # Đối với kiểm tra kích thước chính xác, cần đọc toàn bộ file vào memory hoặc stream và đếm.
        # FastAPI UploadFile.size có sẵn (từ Starlette 0.20.0+)
        if hasattr(upload_file, 'size') and upload_file.size is not None:
             if upload_file.size > max_size_mb * 1024 * 1024:
                print(f"File too large: {upload_file.size / (1024*1024):.2f}MB. Max is {max_size_mb}MB.")
                return None
        else: # Fallback nếu không có `size` attribute (phiên bản cũ hơn hoặc bug)
            # Cần đọc file để kiểm tra, có thể tốn tài nguyên
            contents = await upload_file.read()
            if len(contents) > max_size_mb * 1024 * 1024:
                print(f"File too large (read): {len(contents) / (1024*1024):.2f}MB. Max is {max_size_mb}MB.")
                await upload_file.seek(0) # Quan trọng: đưa con trỏ về đầu để đọc lại khi lưu
                return None
            await upload_file.seek(0) # Quan trọng: đưa con trỏ về đầu để đọc lại khi lưu

    # Tạo tên file duy nhất để tránh ghi đè
    # filename = f"{uuid.uuid4().hex}.{extension}"
    # Hoặc giữ lại một phần tên gốc cho dễ nhận biết (cần sanitize)
    original_stem = pathlib.Path(upload_file.filename).stem
    sanitized_stem = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in original_stem)
    unique_id = uuid.uuid4().hex[:8] # Thêm uuid ngắn
    filename = f"{sanitized_stem}_{unique_id}.{extension}"

    file_path = destination_dir / filename
    
    try:
        with open(file_path, "wb") as buffer:
            # Nếu đã đọc ở trên để kiểm tra size, cần ghi contents
            if 'contents' in locals():
                buffer.write(contents)
            else: # Nếu chưa đọc, thì stream vào
                shutil.copyfileobj(upload_file.file, buffer)
    except Exception as e:
        print(f"Error saving file: {e}")
        return None
    finally:
        await upload_file.close() # Luôn đóng file

    # Trả về đường dẫn tương đối tính từ thư mục STATIC_DIR để dùng với url_for('static', path=...)
    # Ví dụ: UPLOAD_DIR_IMAGES = /app/static/uploads/images
    # STATIC_DIR = /app/static
    # file_path.relative_to(STATIC_DIR) sẽ là uploads/images/filename.ext
    try:
        relative_path = file_path.relative_to(STATIC_DIR)
        # Đảm bảo dùng / làm dấu phân cách path cho URL
        return str(relative_path).replace("\\", "/")
    except ValueError:
        # Trường hợp destination_dir không nằm trong STATIC_DIR (không nên xảy ra với cấu hình hiện tại)
        print("Error: Upload destination is not relative to static directory.")
        return None

async def delete_static_file(relative_path: Optional[str]):
    """
    Xóa file tĩnh dựa trên đường dẫn tương đối từ thư mục static.
    """
    if not relative_path:
        return False
    
    # Chuyển đổi / thành dấu phân cách hệ thống nếu cần (Windows)
    # Tuy nhiên, pathlib thường xử lý tốt
    file_to_delete = STATIC_DIR / relative_path 
    
    try:
        if file_to_delete.is_file():
            file_to_delete.unlink()
            print(f"Deleted static file: {file_to_delete}")
            return True
        else:
            print(f"File not found for deletion: {file_to_delete}")
            return False
    except Exception as e:
        print(f"Error deleting static file {file_to_delete}: {e}")
        return False