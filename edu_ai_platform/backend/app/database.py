import os
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./edu_platform.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


def init_db():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


def get_session_sync():
    return Session(engine)
