import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

load_dotenv()

conn_str = os.environ.get("CONN_STR", "")

engine = create_engine(conn_str)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provide a database session for dependency injection."""
    with Session(engine) as session:
        yield session

