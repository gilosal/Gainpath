"""conftest.py — Test configuration for PaceForge backend tests.

Sets DATABASE_URL to SQLite before any app module is imported,
so the engine is created with SQLite instead of Postgres.
"""
import os

os.environ["APP_ENV"] = "development"
os.environ["APP_PASSWORD"] = "test-password-for-ci"
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared&uri=true"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base


@pytest.fixture(scope="session")
def engine():
    e = create_engine(
        "sqlite:///file::memory:?cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(e)
    yield e
    e.dispose()


@pytest.fixture
def db(engine):
    """Provide a transactional test database session.

    Uses a nested transaction that rolls back after each test so
    data doesn't leak between tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()