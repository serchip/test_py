import os
from typing import Any, Generator

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from fastapi.testclient import TestClient
from fastapi import FastAPI

# from app.utils.app import AppFactory
from app.connects.postgres.base import DBBase
from app.main import get_application
from app.connects.postgres.utils import get_db


SQLALCHEMY_DATABASE_URL = os.getenv('TEST_DATABASE_URL', "sqlite://")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_pre_ping=True#, connect_args={"check_same_thread": False}
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def app() -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case.
    """
    # if not database_exists(engine.url):
    try:
        create_database(engine.url)
    except:
        pass
    DBBase.metadata.create_all(engine)  # Create the tables.
    _app = get_application()
    yield _app
    DBBase.metadata.drop_all(engine)


@pytest.fixture
def db_session(app: FastAPI) -> Generator[Session, Any, None]:
    """
    Creates a fresh sqlalchemy session for each test that operates in a
    transaction. The transaction is rolled back at the end of each test ensuring
    a clean state.
    """

    # connect to the database
    connection = engine.connect()
    # begin a non-ORM transaction
    transaction = connection.begin()
    # bind an individual Session to the connection
    session = Session(bind=connection)
    yield session  # use the session in tests.
    session.close()
    # rollback - everything that happened with the
    # Session above (including calls to commit())
    # is rolled back.
    transaction.rollback()
    # return connection to the Engine
    connection.close()

@pytest.fixture()
def client(app: FastAPI, db_session: Session) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
