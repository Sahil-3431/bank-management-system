from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL


# ============================================================
# DATABASE URL CHECK
# ============================================================

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured. "
        "Please add DATABASE_URL to your .env file."
    )


# ============================================================
# DATABASE URL - FORCE PSYCOPG2
# ============================================================

# SQLAlchemy 2.1 may select psycopg (v3) for a PostgreSQL URL.
# This project uses psycopg2-binary, so explicitly use psycopg2.

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1
    )


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# DATABASE SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# BASE CLASS
# ============================================================

Base = declarative_base()


# ============================================================
# DATABASE SESSION HELPER
# ============================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():
    from models import (
        User,
        Customer,
        Account,
        Transaction,
    )

    Base.metadata.create_all(bind=engine)