# DevOps FastAPI Blog

This is a blog project built with FastAPI, SQLModel, and Jinja2 templates, featuring functionalities like post management, user management, comments, tags, image uploads, and a Dark Mode interface. This project is hosted at [https://github.com/kiendo96/devops-blog-fastapi](https://github.com/kiendo96/devops-blog-fastapi).

## Key Features (Examples)

* Post Management (CRUD)
* User Management (CRUD, Admin role)
* Comment System
* Tag Management
* User Authentication (Register, Login, Logout) using JWT
* Featured image upload for posts and user profile pictures
* Admin Panel for website content management
* Responsive Frontend with Dark Mode
* Database migrations with Alembic
* Packaged with Docker

## Technologies Used

* **Backend:** Python, FastAPI, SQLModel (Pydantic + SQLAlchemy), Uvicorn
* **Frontend:** Jinja2 Templates, HTML, CSS, JavaScript, Bootstrap 5
* **Database:** SQLite (can be easily switched to PostgreSQL, MySQL)
* **Migrations:** Alembic
* **Deployment (Example):** Docker

## Prerequisites

* [Git](https://git-scm.com/)
* [Docker](https://www.docker.com/get-started) (recommended for deployment)
* [Python](https://www.python.org/downloads/) (version 3.9+ for local development)
* `pip` (Python package installer)

## Setup and Running the Project with Docker (Recommended)

This is the easiest way to run the project and ensure a consistent environment.

1.  **Clone Repository:**
    ```bash
    git clone [https://github.com/kiendo96/devops-blog-fastapi.git](https://github.com/kiendo96/devops-blog-fastapi.git)
    cd devops-blog-fastapi
    ```

2.  **Build Docker Image:**
    From the project's root directory (where the `Dockerfile` is located), run:
    ```bash
    docker build -t devops_fastapi_blog_image .
    ```
    *(You can replace `devops_fastapi_blog_image` with your preferred image name)*

3.  **Run Docker Container:**
    ```bash
    docker run -d \
        -p 8000:8000 \
        -v devops_blog_data:/app_code/data \
        -v devops_blog_uploads:/app_code/app/static/uploads \
        -e SECRET_KEY="YOUR_VERY_STRONG_RANDOM_SECRET_KEY_HERE" \
        --name devops_fastapi_blog_container \
        devops_fastapi_blog_image
    ```
    **Explanation:**
    * `-d`: Run the container in detached mode (background).
    * `-p 8000:8000`: Map port 8000 of the host machine to port 8000 of the container.
    * `-v devops_blog_data:/app_code/data`: Mount a named volume `devops_blog_data` to the `/app_code/data` directory in the container. The SQLite database file (`blog.db`) will be stored here, ensuring data persistence.
    * `-v devops_blog_uploads:/app_code/app/static/uploads`: Mount a named volume `devops_blog_uploads` to the `/app_code/app/static/uploads` directory in the container. User-uploaded image files will be stored here.
    * `-e SECRET_KEY="..."`: **VERY IMPORTANT!** Set the `SECRET_KEY` environment variable for the FastAPI application. Replace `"YOUR_VERY_STRONG_RANDOM_SECRET_KEY_HERE"` with your own strong, random, and secret string. You can generate one by running `python -c 'import secrets; print(secrets.token_hex(32))'` in your terminal.
    * `--name devops_fastapi_blog_container`: Assign a name to the container.
    * `devops_fastapi_blog_image`: The name of the Docker image you built.

    After the container starts, Alembic migrations will automatically run to update the database schema if necessary.

4.  **Access the application:**
    Open your browser and go to `http://localhost:8000`.

## Creating an Admin Account

After the project is running (either via Docker or locally), you need to create an admin account to access the Admin Panel.

**Method 1: If running with Docker (Recommended)**

1.  Find the ID or name of your running container:
    ```bash
    docker ps
    ```
    (You named it `devops_fastapi_blog_container`)

2.  Execute the `create_admin.py` script inside the container:
    ```bash
    docker exec -it devops_fastapi_blog_container python scripts/create_admin.py
    ```
    The script will prompt you to enter the username, email, and password for the admin account.

**Method 2: If running locally (Local Development)**

1.  Ensure you are in the project's root directory and have activated your virtual environment.
2.  Run the script:
    ```bash
    python scripts/create_admin.py
    ```
    The script will prompt you for the necessary information. The `data/blog.db` file will be updated.

After successful creation, you can log in with the newly created admin account and access the admin panel at `http://localhost:8000/admin`.

## Local Development Guide (Optional)

If you prefer to run the project directly on your machine without Docker:

1.  **Clone Repository (if you haven't already):**
    ```bash
    git clone [https://github.com/kiendo96/devops-blog-fastapi.git](https://github.com/kiendo96/devops-blog-fastapi.git)
    cd devops-blog-fastapi
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(First time) Create `data` directory:**
    If it doesn't exist, create a `data` directory in the project root. The SQLite database file will be stored here.
    ```bash
    mkdir data
    ```
    The `app/static/uploads/images` directory should also be created if it doesn't exist (the `app/utils/file_upload.py` script will attempt to create it on the first upload).

5.  **Run Alembic Migrations:**
    To create or update the database schema:
    ```bash
    alembic upgrade head
    ```

6.  **(Optional) Create `.env` file:**
    Create a `.env` file in the project root and define environment variables if needed, for example:
    ```env
    SECRET_KEY="YOUR_LOCAL_STRONG_SECRET_KEY_HERE"
    # Other environment variables if any
    ```
    The `app/core/config.py` file will read these variables. **Remember to add `.env` to your `.gitignore` file!**

7.  **Run Uvicorn Server:**
    From the project's root directory, run:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    * `--reload`: Automatically reloads the server on code changes (for development only).

8.  **Create Admin Account:**
    Run the script as described in the "Creating an Admin Account" section (Method 2).

9.  **Access the application:**
    Open your browser and go to `http://localhost:8000`.

## Project Structure (Example)

```text
.
├── alembic/                    # Directory for Alembic migrations
├── alembic.ini                 # Alembic configuration file
├── app/                        # Main application code directory
│   ├── api/                    # API endpoints (v1)
│   ├── core/                   # Configuration, security
│   ├── crud/                   # CRUD functions (Create, Read, Update, Delete)
│   ├── db/                     # Database session configuration
│   ├── models/                 # SQLModel models (database schema and Pydantic models)
│   ├── routers/                # Routers for frontend and admin pages
│   ├── static/                 # Static files (CSS, JS, images, uploads)
│   │   ├── css/
│   │   ├── js/
│   │   └── uploads/
│   │       └── images/         # Storage for uploaded images
│   ├── templates/              # Jinja2 templates
│   │   ├── admin/
│   │   ├── auth/
│   │   └── posts/
│   ├── utils/                  # Utility functions (e.g., file_upload.py)
│   └── main.py                 # Main FastAPI app initialization file
├── data/                       # Directory for database (e.g., blog.db) - gitignored
├── scripts/                    # Utility scripts (e.g., create_admin.py)
├── .dockerignore               # Files to ignore for Docker build
├── .gitignore                  # Files to ignore for Git
├── Dockerfile                  # Docker image definition file
├── README.md                   # This file
├── requirements.txt            # Python dependencies list
└── env.py                      # Alembic environment configuration file
Good luck with your project