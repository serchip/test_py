from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from app.settings import POSTGRES_CONNECT


SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{POSTGRES_CONNECT.username}:"
    f"{POSTGRES_CONNECT.password}@{POSTGRES_CONNECT.hostname}:"
    f"{POSTGRES_CONNECT.port}/{POSTGRES_CONNECT.path[1:]}"
)


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
#    connect_args={"check_same_thread": False},
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DBBase = declarative_base()
