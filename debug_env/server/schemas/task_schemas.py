"""
Pydantic schemas for task API responses and requests.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class TaskResponse(BaseModel):
    """Response model for a single task."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    difficulty: str
    bug_type: str
    files: List[str]
    tools: Optional[List[str]] = None
    scenario_type: Optional[str] = None
    participants: Optional[List[Dict[str, Any]]] = None
    etag: str
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Response model for paginated task list."""

    items: List[TaskResponse]
    etag: str
    nextPageToken: Optional[str] = None
    nextSyncToken: Optional[str] = None


class EpisodeResponse(BaseModel):
    """Response model for a single episode."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    user_id: str
    workdir: Optional[str] = None
    status: str
    pass_rate: Optional[float] = None
    etag: str
    created_at: datetime
    updated_at: datetime


class EpisodeListResponse(BaseModel):
    """Response model for paginated episode list."""

    items: List[EpisodeResponse]
    nextPageToken: Optional[str] = None


class EpisodeCreateRequest(BaseModel):
    """Request model to create an episode."""

    task_id: str


class EpisodePatchRequest(BaseModel):
    """Request model to update an episode."""

    status: Optional[str] = None
    pass_rate: Optional[float] = None


class WatchChannelResponse(BaseModel):
    """Response model for a watch channel."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    user_id: str
    webhook_address: str
    webhook_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime


class WatchChannelRequest(BaseModel):
    """Request model to create a watch channel."""

    id: str
    address: str
    token: Optional[str] = None
