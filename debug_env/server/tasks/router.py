"""
Tasks API endpoints
Provides task metadata, episode management, and source file access for the debug-env benchmark.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import ValidationError
from sqlalchemy.orm import Session

from debug_env.server.tasks.data import get_available_task_ids, get_task_by_id, validate_task_id
from debug_env.server.tasks.loader import TaskLoader
from debug_env.server.database.db import get_db
from debug_env.server.database.managers.task_manager import get_task_manager
from debug_env.server.schemas.task_schemas import (
    TaskListResponse,
    TaskResponse,
    EpisodeResponse,
    EpisodeListResponse,
    EpisodeCreateRequest,
    EpisodePatchRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _format_validation_error(e: ValidationError) -> str:
    """Format a Pydantic ValidationError into a human-readable string."""
    messages = []
    for error in e.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        messages.append(f"{field}: {error['msg']}")
    return "Validation failed: " + "; ".join(messages)


@router.get("", response_model=Dict[str, Any])
async def list_tasks(
    db: Session = Depends(get_db),
    maxResults: int = 50,
    pageToken: str = None,
    syncToken: str = None,
):
    """
    Returns metadata for all available debug tasks with pagination support.

    Query Parameters:
      - maxResults: Maximum tasks per page (default: 50)
      - pageToken: Pagination token from previous response
      - syncToken: Sync token for incremental updates

    GET /tasks
    """
    try:
        # Get user_id from header (default to "default_user" if not provided)
        user_id = "default_user"

        # Use TaskManager for listing with pagination
        manager = get_task_manager(db, user_id)
        response = manager.list_tasks(
            max_results=maxResults,
            page_token=pageToken,
            sync_token=syncToken,
        )

        # Convert to dict response matching schema
        return {
            "etag": response.etag,
            "items": [TaskResponse.model_validate(item).model_dump() for item in response.items],
            "nextPageToken": response.nextPageToken,
            "nextSyncToken": response.nextSyncToken,
        }
    except ValueError as e:
        logger.error(f"Validation error listing tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while listing tasks",
        )


@router.get("/{taskId}", response_model=Dict[str, Any])
async def get_task(taskId: str):
    """
    Returns metadata for a specific debug task.

    GET /tasks/{taskId}
    """
    try:
        if not validate_task_id(taskId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{taskId}' not found. Available: {get_available_task_ids()}",
            )
        task = get_task_by_id(taskId)
        logger.info(f"Retrieved task metadata for '{taskId}'")
        return task
    except HTTPException:
        raise
    except ValidationError as e:
        # Handle unexpected schema validation errors
        logger.error(f"Schema validation error for task '{taskId}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_format_validation_error(e),
        )
    except Exception as e:
        logger.error(f"Error getting task '{taskId}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving task",
        )


@router.get("/{taskId}/files", response_model=List[str])
async def list_task_files(taskId: str):
    """
    Returns the list of editable source files for a task (excludes test files).

    GET /tasks/{taskId}/files
    """
    try:
        if not validate_task_id(taskId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{taskId}' not found. Available: {get_available_task_ids()}",
            )
        files = TaskLoader.list_source_files(taskId)
        logger.info(f"Listed {len(files)} source files for task '{taskId}'")
        return files
    except HTTPException:
        raise
    except ValueError as e:
        # Handle business logic validation errors (invalid task ID)
        logger.error(f"Validation error listing files for task '{taskId}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task or request parameters")
    except FileNotFoundError as e:
        # Task is registered but files are missing from disk
        logger.error(f"Task files missing on disk for '{taskId}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while listing task files",
        )
    except Exception as e:
        logger.error(f"Error listing files for task '{taskId}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while listing task files",
        )


@router.get("/{taskId}/files/{filename}", response_model=Dict[str, str])
async def get_task_file(taskId: str, filename: str):
    """
    Returns the canonical (pre-episode) content of a source file.

    Use this to inspect the original broken code before starting an episode.
    During an episode, use the read_file tool via POST /step instead.

    GET /tasks/{taskId}/files/{filename}
    """
    try:
        if not validate_task_id(taskId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{taskId}' not found. Available: {get_available_task_ids()}",
            )
        content = TaskLoader.read_source_file(taskId, filename)
        logger.info(f"Read source file '{filename}' for task '{taskId}'")
        return {"task_id": taskId, "filename": filename, "content": content}
    except HTTPException:
        raise
    except ValueError as e:
        # Handle business logic validation errors (invalid filename, path traversal)
        logger.error(f"Validation error reading file '{filename}' for task '{taskId}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename or request parameters")
    except FileNotFoundError as e:
        # File not found within the task
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading file '{filename}' for task '{taskId}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while reading task file",
        )


# ── Episode Management Endpoints ───────────────────────────────────────────


@router.post("/{taskId}/episodes", response_model=Dict[str, Any])
async def create_episode(
    taskId: str,
    db: Session = Depends(get_db),
):
    """
    Create a new episode (task run) for the current user.

    POST /tasks/{taskId}/episodes

    Returns:
      - id: Episode identifier (uuid4)
      - task_id: Task identifier
      - status: "active"
      - workdir: Path to working directory with task files
      - etag: Cache validation tag
    """
    try:
        if not validate_task_id(taskId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{taskId}' not found",
            )

        user_id = "default_user"
        manager = get_task_manager(db, user_id)

        # Load task files into temp directory
        workdir = TaskLoader.load(taskId)

        # Create episode record
        episode = manager.create_episode(taskId, workdir)

        logger.info(f"Created episode {episode.id} for task {taskId}")
        return EpisodeResponse.model_validate(episode).model_dump()

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating episode for task {taskId}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating episode for task {taskId}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating episode",
        )


@router.get("/{taskId}/episodes", response_model=Dict[str, Any])
async def list_episodes(
    taskId: str,
    db: Session = Depends(get_db),
    maxResults: int = 50,
    pageToken: str = None,
):
    """
    List episodes for a task with pagination.

    GET /tasks/{taskId}/episodes

    Query Parameters:
      - maxResults: Maximum episodes per page (default: 50)
      - pageToken: Pagination token from previous response
    """
    try:
        if not validate_task_id(taskId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{taskId}' not found",
            )

        user_id = "default_user"
        manager = get_task_manager(db, user_id)

        response = manager.list_episodes(taskId, max_results=maxResults, page_token=pageToken)

        return {
            "items": [EpisodeResponse.model_validate(item).model_dump() for item in response.items],
            "nextPageToken": response.nextPageToken,
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error listing episodes for task {taskId}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing episodes for task {taskId}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while listing episodes",
        )


@router.get("/{taskId}/episodes/{episodeId}", response_model=Dict[str, Any])
async def get_episode(
    taskId: str,
    episodeId: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific episode.

    GET /tasks/{taskId}/episodes/{episodeId}
    """
    try:
        if not validate_task_id(taskId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{taskId}' not found",
            )

        user_id = "default_user"
        manager = get_task_manager(db, user_id)

        episode = manager.get_episode(taskId, episodeId)
        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode '{episodeId}' not found for task '{taskId}'",
            )

        return EpisodeResponse.model_validate(episode).model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving episode {episodeId} for task {taskId}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving episode",
        )


@router.patch("/{taskId}/episodes/{episodeId}", response_model=Dict[str, Any])
async def update_episode(
    taskId: str,
    episodeId: str,
    request: EpisodePatchRequest,
    db: Session = Depends(get_db),
):
    """
    Update an episode's status and/or pass_rate.

    PATCH /tasks/{taskId}/episodes/{episodeId}

    Request Body:
      - status: Optional, new status ("active", "passed", "failed", "abandoned")
      - pass_rate: Optional, pass rate (0.0-1.0)
    """
    try:
        if not validate_task_id(taskId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{taskId}' not found",
            )

        user_id = "default_user"
        manager = get_task_manager(db, user_id)

        # Get current episode
        episode = manager.get_episode(taskId, episodeId)
        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode '{episodeId}' not found for task '{taskId}'",
            )

        # Update with provided fields
        status = request.status if request.status else episode.status
        pass_rate = request.pass_rate if request.pass_rate is not None else episode.pass_rate

        updated_episode = manager.update_episode(taskId, episodeId, status, pass_rate)

        logger.info(f"Updated episode {episodeId} for task {taskId}")
        return EpisodeResponse.model_validate(updated_episode).model_dump()

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating episode {episodeId}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating episode {episodeId}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating episode",
        )
