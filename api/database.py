import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Local dev (and the sandbox test suite) uses a SQLite file with no setup
# required. Real deployment (Vercel) sets DATABASE_URL to a Postgres
# connection string (e.g. Neon/Supabase) via environment variable - SQLite
# files don't persist reliably on serverless filesystems.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./jony_crm.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Postgres on serverless: each function invocation is short-lived, and
    # Neon/Supabase's pooled connection string already does pooling via
    # PgBouncer in front of the database - so SQLAlchemy shouldn't keep its
    # own persistent pool on top of that (NullPool opens/closes per use).
    # pool_pre_ping guards against stale connections from cold starts.
    engine = create_engine(DATABASE_URL, poolclass=NullPool, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
