from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


db_url = settings.get_database_url()
is_sqlite = db_url.startswith("sqlite")

engine_args = {
    "pool_pre_ping": True,
}

if is_sqlite:
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_recycle"] = 3600
    engine_args["connect_args"] = {"connect_timeout": 3}

try:
    engine = create_engine(db_url, **engine_args)
    if not is_sqlite:
        with engine.connect() as probe_conn:
            probe_conn.execute(text("SELECT 1"))
except Exception as exc:
    print(f"[DATABASE NOTICE] Connection to {db_url} failed ({exc}). Falling back to local SQLite database.")
    db_url = "sqlite:///./inboundshield.db"
    is_sqlite = True
    engine = create_engine(db_url, pool_pre_ping=True, connect_args={"check_same_thread": False})

if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db():
    import app.models.models  # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
