"""
SQLAlchemy ORM models for tasks, episodes, and watch channels.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func

from debug_env.server.database.db import Base


class TaskRecord(Base):
    """
    Task record — mirrors TASK_REGISTRY in database.

    Each row represents a debuggable task available in the benchmark.
    Seeded from TASK_REGISTRY at application startup.
    """

    __tablename__ = "task_records"

    id = Column(String, primary_key=True, index=True)  # e.g., "task1"
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # e.g., "easy", "medium", "hard"
    bug_type = Column(String, nullable=False)  # e.g., "syntax", "logic", "type_error"
    files = Column(JSON, nullable=False)  # List of filenames
    tools = Column(JSON, nullable=True)  # List of available tools for this task
    scenario_type = Column(String, nullable=True)  # e.g., "code_review", "cross_team_collaboration"
    participants = Column(JSON, nullable=True)  # List of participant dicts for multi-user tasks
    etag = Column(String, nullable=False)  # Cache validation tag
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<TaskRecord(id={self.id}, title={self.title}, difficulty={self.difficulty})>"


class EpisodeRecord(Base):
    """
    Episode record — tracks each task run (reset/step sequence).

    One row created per TaskLoader.load() call (when DebugEnvironment.reset() is called).
    Tracks workdir, status, and pass_rate for the episode lifecycle.
    """

    __tablename__ = "episode_records"

    id = Column(String, primary_key=True, index=True)  # UUID4 string
    task_id = Column(String, nullable=False, index=True)  # e.g., "task1" (FK to task_records.id)
    user_id = Column(String, nullable=False, index=True)  # e.g., "default_user" or from X-User-Id header
    workdir = Column(String, nullable=True)  # Path to temp directory with task files
    status = Column(
        String,
        nullable=False,
        default="active",
        index=True,
    )  # "active", "passed", "failed", "abandoned"
    pass_rate = Column(Float, nullable=True)  # 0.0 to 1.0, or None if not completed
    etag = Column(String, nullable=False)  # Cache validation tag
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<EpisodeRecord(id={self.id}, task_id={self.task_id}, status={self.status})>"


class WatchChannel(Base):
    """
    Watch channel record — tracks webhook subscriptions for task/episode state changes.

    Allows clients to subscribe to notifications when tasks or episodes change.
    Lightweight structure for future expansion of notification features.
    """

    __tablename__ = "watch_channels"

    id = Column(String, primary_key=True, index=True)  # Client-provided ID
    task_id = Column(String, nullable=False, index=True)  # Task being watched
    user_id = Column(String, nullable=False, index=True)  # User who set up the watch
    webhook_address = Column(String, nullable=False)  # URL to POST notifications to
    webhook_token = Column(String, nullable=True)  # Optional auth token for webhook
    expires_at = Column(DateTime, nullable=True, index=True)  # When this watch expires
    is_active = Column(Boolean, default=True, nullable=False)  # Whether watch is currently active
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<WatchChannel(id={self.id}, task_id={self.task_id}, is_active={self.is_active})>"
