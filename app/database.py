import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


def database_url():
    return os.environ.get("WORKBENCH_DATABASE_URL", "sqlite:///./workbench.db")


def make_engine(url):
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 5})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


def session_factory(engine):
    return sessionmaker(engine, expire_on_commit=False)
