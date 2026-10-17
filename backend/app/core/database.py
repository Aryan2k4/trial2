from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings
from app.core.cache_revision import advance_revision

connect_args = {"check_same_thread": False, "timeout": 15} if settings.DATABASE_URL.startswith("sqlite") else {}
# Bound connections for small hosted databases; recycle stale connections
# after idle periods and validate them when checked out of the pool.
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_size=5, max_overflow=5, pool_timeout=30, pool_pre_ping=True, pool_recycle=300)

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite's default journal mode serializes writers hard enough that
    # ordinary concurrent traffic — the dashboard's 30s background poll
    # firing in 4 open tabs, an agent investigation writing an alert,
    # someone adding/deleting a record in Manage Dataset — can trip
    # "database is locked" errors that surface to the browser as a
    # random, intermittent failure even though nothing is actually
    # broken. WAL mode lets reads and writes run concurrently instead
    # of blocking each other, and busy_timeout makes any write that
    # still collides retry for 15s instead of failing immediately.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
event.listen(SessionLocal, "after_commit", advance_revision)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import time
    import logging
    log = logging.getLogger(__name__)

    # Import models so they're registered on Base before create_all
    from app.models import energy_models  # noqa
    from app.models import maintenance_models  # noqa
    from app.models import occupancy_models  # noqa
    from app.models import security_models  # noqa
    from app.models import cost_models  # noqa
    from app.models import auth_models  # noqa
    from app.models import agent_memory_models  # noqa

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            # create_all does not add a new index to an existing table.
            for index in security_models.AccessEvent.__table__.indexes:
                if index.name == "ix_sec_emp_ap_ts":
                    index.create(bind=engine, checkfirst=True)
            break
        except Exception as e:
            if attempt == max_retries:
                log.error(f"Failed to initialize database tables after {max_retries} attempts: {e}")
                raise
            log.warning(f"Database connection attempt {attempt} failed ({e}), retrying in 2s...")
            time.sleep(2)
