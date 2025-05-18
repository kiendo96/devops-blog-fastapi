from sqlmodel import create_engine, SQLModel, Session
from app.core.config import settings

connect_args = {"check_same_thread": False}
engine = create_engine(settings.DATABASE_URL, echo=True, connect_args=connect_args)

def create_db_and_tables():
    pass

def get_session_local():
     with Session(engine) as session:
        yield session