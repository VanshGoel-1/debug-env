"""
Database configuration and session management for debug_env.

Provides SQLite database engine, session factory, and FastAPI dependency injection.
"""

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger(__name__)

# Database path: debug_env.db in the server directory
DB_PATH = Path(__file__).parent.parent / "debug_env.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # SQLite specific
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative base for ORM models
Base = declarative_base()


def get_db() -> Session:
    """
    FastAPI dependency: yields a database session.

    Usage:
        async def my_endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database: create all tables and seed task registry.

    Called on application startup via @app.on_event("startup").
    """
    # Import models to register them with Base
    from debug_env.server.database.models.task import TaskRecord, EpisodeRecord, WatchChannel  # noqa: F401

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at {DB_PATH}")

    # Seed TASK_REGISTRY into task_records table if not already present
    _seed_task_registry()


def _seed_task_registry() -> None:
    """Seed the task_records table with TASK_REGISTRY on startup."""
    from debug_env.server.database.models.task import TaskRecord
    from debug_env.server.tasks.data import TASK_REGISTRY
    from datetime import datetime
    from uuid import uuid4

    db = SessionLocal()
    try:
        # Check if tasks already exist
        existing_count = db.query(TaskRecord).count()
        if existing_count > 0:
            logger.debug(f"Task registry already seeded ({existing_count} tasks)")
            return

        # Seed each task from TASK_REGISTRY
        now = datetime.utcnow()
        for task_id, task_data in TASK_REGISTRY.items():
            task_record = TaskRecord(
                id=task_id,
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                difficulty=task_data.get("difficulty", ""),
                bug_type=task_data.get("bug_type", ""),
                files=task_data.get("files", []),
                tools=task_data.get("tools"),
                scenario_type=task_data.get("scenario_type"),
                participants=task_data.get("participants"),
                etag=f'"{uuid4()}"',
                created_at=now,
                updated_at=now,
            )
            db.add(task_record)

        db.commit()
        logger.info(f"Seeded {len(TASK_REGISTRY)} tasks into database")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding task registry: {e}")
        raise
    finally:
        db.close()
