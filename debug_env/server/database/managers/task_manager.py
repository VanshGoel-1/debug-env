"""
Task Manager — Manages task metadata, episodes, and watch channels.

Follows the ACLManager pattern: class-based CRUD with user scoping, pagination,
sync tokens, and ETags for cache validation.
"""

import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from debug_env.server.database.models.task import TaskRecord, EpisodeRecord, WatchChannel

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manages task operations with user-scoped access control.

    Args:
        db: SQLAlchemy Session
        user_id: User identifier for scoping operations
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def list_tasks(
        self,
        max_results: int = 50,
        page_token: Optional[str] = None,
        sync_token: Optional[str] = None,
    ) -> "TaskListResponse":
        """
        List tasks with pagination and sync token support.

        Args:
            max_results: Maximum number of tasks per page (1-250, default 50)
            page_token: Pagination token from previous response
            sync_token: Sync token for incremental updates

        Returns:
            TaskListResponse with items, nextPageToken, nextSyncToken
        """
        try:
            # Handle sync token for incremental synchronization
            if sync_token:
                return self._handle_sync_request(sync_token, max_results)

            # Base query: all tasks (not user-scoped)
            query = self.db.query(TaskRecord).order_by(TaskRecord.id)

            # Handle pagination with base64 offset token
            offset = 0
            if page_token:
                try:
                    offset = int(base64.b64decode(page_token).decode("utf-8"))
                except (ValueError, TypeError):
                    raise ValueError("Invalid pageToken")

            # Get one extra to determine if there's a next page
            items = query.offset(offset).limit(max_results + 1).all()

            has_next_page = len(items) > max_results
            if has_next_page:
                items = items[:max_results]
                next_page_token = base64.b64encode(
                    str(offset + max_results).encode("utf-8")
                ).decode("utf-8")
            else:
                next_page_token = None

            # Generate next sync token based on latest update
            latest_updated = (
                self.db.query(TaskRecord.updated_at)
                .order_by(desc(TaskRecord.updated_at))
                .first()
            )

            next_sync_token = None
            if latest_updated and latest_updated[0]:
                sync_data = {
                    "timestamp": latest_updated[0].isoformat(),
                    "user_id": self.user_id,
                }
                next_sync_token = base64.b64encode(
                    json.dumps(sync_data).encode("utf-8")
                ).decode("utf-8")

            # Generate collection etag
            etag = f'"{uuid4()}"'

            return TaskListResponse(
                etag=etag,
                items=items,
                nextPageToken=next_page_token,
                nextSyncToken=next_sync_token,
            )

        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            raise

    def _handle_sync_request(
        self, sync_token: str, max_results: int
    ) -> "TaskListResponse":
        """
        Handle incremental synchronization request.

        Args:
            sync_token: Sync token from previous response
            max_results: Maximum items to return

        Returns:
            TaskListResponse with changes since sync token
        """
        try:
            # Decode sync token
            sync_data = json.loads(base64.b64decode(sync_token).decode("utf-8"))
            last_sync_time = datetime.fromisoformat(sync_data["timestamp"])

            # Check if sync token is too old (7-day expiration)
            if (datetime.utcnow() - last_sync_time).days > 7:
                raise ValueError("Sync token expired")

            # Query for changes since last sync
            query = (
                self.db.query(TaskRecord)
                .filter(TaskRecord.updated_at > last_sync_time)
                .order_by(TaskRecord.updated_at, TaskRecord.id)
            )

            items = query.limit(max_results + 1).all()

            has_more = len(items) > max_results
            if has_more:
                items = items[:max_results]

            # Generate new sync token
            next_sync_token = None
            if items:
                latest_time = max(item.updated_at for item in items)
                sync_data = {
                    "timestamp": latest_time.isoformat(),
                    "user_id": self.user_id,
                }
                next_sync_token = base64.b64encode(
                    json.dumps(sync_data).encode("utf-8")
                ).decode("utf-8")
            else:
                # No changes, return same sync token
                next_sync_token = sync_token

            # Generate etag
            etag = f'"{uuid4()}"'

            return TaskListResponse(
                etag=etag,
                items=items,
                nextPageToken=None,
                nextSyncToken=next_sync_token,
            )

        except json.JSONDecodeError:
            raise ValueError("Invalid sync token format")
        except Exception as e:
            logger.error(f"Error handling sync request: {e}")
            raise

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """
        Retrieve a specific task by ID.

        Args:
            task_id: Task identifier (e.g., "task1")

        Returns:
            TaskRecord or None if not found
        """
        return self.db.query(TaskRecord).filter(TaskRecord.id == task_id).first()

    def create_episode(self, task_id: str, workdir: str) -> EpisodeRecord:
        """
        Create a new episode (task run) for a user.

        Args:
            task_id: Task identifier
            workdir: Path to working directory with task files

        Returns:
            Created EpisodeRecord
        """
        try:
            # Verify task exists
            task = self.get_task(task_id)
            if not task:
                raise ValueError(f"Task '{task_id}' not found")

            # Create episode
            episode_id = str(uuid4())
            episode = EpisodeRecord(
                id=episode_id,
                task_id=task_id,
                user_id=self.user_id,
                workdir=workdir,
                status="active",
                etag=f'"{uuid4()}"',
            )
            self.db.add(episode)
            self.db.commit()
            self.db.refresh(episode)

            logger.info(
                f"Created episode {episode_id} for task {task_id}, user {self.user_id}"
            )
            return episode

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating episode: {e}")
            raise

    def get_episode(self, task_id: str, episode_id: str) -> Optional[EpisodeRecord]:
        """
        Retrieve a specific episode.

        Args:
            task_id: Task identifier
            episode_id: Episode identifier

        Returns:
            EpisodeRecord or None if not found
        """
        return (
            self.db.query(EpisodeRecord)
            .filter(
                and_(
                    EpisodeRecord.id == episode_id,
                    EpisodeRecord.task_id == task_id,
                    EpisodeRecord.user_id == self.user_id,
                )
            )
            .first()
        )

    def update_episode(
        self, task_id: str, episode_id: str, status: str, pass_rate: Optional[float] = None
    ) -> Optional[EpisodeRecord]:
        """
        Update an episode's status and pass rate.

        Args:
            task_id: Task identifier
            episode_id: Episode identifier
            status: New status ("active", "passed", "failed", "abandoned")
            pass_rate: Pass rate (0.0-1.0) if completed

        Returns:
            Updated EpisodeRecord or None if not found
        """
        try:
            episode = self.get_episode(task_id, episode_id)
            if not episode:
                return None

            episode.status = status
            if pass_rate is not None:
                episode.pass_rate = pass_rate
            episode.etag = f'"{uuid4()}"'
            episode.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(episode)

            logger.info(
                f"Updated episode {episode_id} status to {status} (pass_rate={pass_rate})"
            )
            return episode

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating episode: {e}")
            raise

    def list_episodes(
        self, task_id: str, max_results: int = 50, page_token: Optional[str] = None
    ) -> "EpisodeListResponse":
        """
        List episodes for a task with pagination.

        Args:
            task_id: Task identifier
            max_results: Maximum items per page
            page_token: Pagination token

        Returns:
            EpisodeListResponse with items and nextPageToken
        """
        try:
            # Base query: user-scoped
            query = (
                self.db.query(EpisodeRecord)
                .filter(
                    and_(EpisodeRecord.task_id == task_id, EpisodeRecord.user_id == self.user_id)
                )
                .order_by(EpisodeRecord.created_at, EpisodeRecord.id)
            )

            # Handle pagination
            offset = 0
            if page_token:
                try:
                    offset = int(base64.b64decode(page_token).decode("utf-8"))
                except (ValueError, TypeError):
                    raise ValueError("Invalid pageToken")

            items = query.offset(offset).limit(max_results + 1).all()

            has_next_page = len(items) > max_results
            if has_next_page:
                items = items[:max_results]
                next_page_token = base64.b64encode(
                    str(offset + max_results).encode("utf-8")
                ).decode("utf-8")
            else:
                next_page_token = None

            return EpisodeListResponse(items=items, nextPageToken=next_page_token)

        except Exception as e:
            logger.error(f"Error listing episodes: {e}")
            raise

    def watch_task(self, task_id: str, watch_request: Dict[str, Any]) -> WatchChannel:
        """
        Set up a watch channel for task state changes.

        Args:
            task_id: Task identifier
            watch_request: Dict with 'id', 'address', 'token' (optional)

        Returns:
            Created WatchChannel
        """
        try:
            # Verify task exists
            task = self.get_task(task_id)
            if not task:
                raise ValueError(f"Task '{task_id}' not found")

            # Check for duplicate watch ID
            existing = self.db.query(WatchChannel).filter(
                WatchChannel.id == watch_request["id"]
            ).first()
            if existing:
                raise ValueError(f"Watch channel with ID {watch_request['id']} already exists")

            # Create watch channel (24 hour default expiration)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            channel = WatchChannel(
                id=watch_request["id"],
                task_id=task_id,
                user_id=self.user_id,
                webhook_address=watch_request["address"],
                webhook_token=watch_request.get("token"),
                expires_at=expires_at,
                is_active=True,
            )
            self.db.add(channel)
            self.db.commit()
            self.db.refresh(channel)

            logger.info(f"Created watch channel {watch_request['id']} for task {task_id}")
            return channel

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating watch channel: {e}")
            raise

    def cleanup_expired_channels(self) -> int:
        """
        Clean up expired watch channels for this user.

        Returns:
            Number of channels cleaned up
        """
        try:
            current_time = datetime.utcnow()

            expired_channels = (
                self.db.query(WatchChannel)
                .filter(
                    and_(
                        WatchChannel.user_id == self.user_id,
                        WatchChannel.expires_at < current_time,
                        WatchChannel.is_active == True,
                    )
                )
                .all()
            )

            cleanup_count = 0
            for channel in expired_channels:
                channel.is_active = False
                cleanup_count += 1

            if cleanup_count > 0:
                self.db.commit()
                logger.info(f"Cleaned up {cleanup_count} expired watch channels for user {self.user_id}")

            return cleanup_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up expired channels: {e}")
            return 0


# Response models (simple classes matching the pattern)
class TaskListResponse:
    def __init__(
        self,
        etag: str,
        items: List[TaskRecord],
        nextPageToken: Optional[str] = None,
        nextSyncToken: Optional[str] = None,
    ):
        self.etag = etag
        self.items = items
        self.nextPageToken = nextPageToken
        self.nextSyncToken = nextSyncToken


class EpisodeListResponse:
    def __init__(self, items: List[EpisodeRecord], nextPageToken: Optional[str] = None):
        self.items = items
        self.nextPageToken = nextPageToken


def get_task_manager(db: Session, user_id: str) -> TaskManager:
    """Factory function to create a TaskManager instance."""
    return TaskManager(db, user_id)
