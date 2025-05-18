from pydantic_settings import BaseSettings
import os
import pathlib

class Settings(BaseSettings):
    PROJECT_NAME: str = "My Blog API"
    API_V1_STR: str = "/api/v1"
    
    DATA_DIR: pathlib.Path = pathlib.Path("./data")
    SQLITE_DB_FILE: str = str(DATA_DIR / "blog.db")
    DATABASE_URL: str = f"sqlite:///{SQLITE_DB_FILE}"
    
    SECRET_KEY: str = "ThisIsMySecretDemo@123213"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
    
settings = Settings()