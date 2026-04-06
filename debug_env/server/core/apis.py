"""
Core API endpoints for debug-env.
Handles health checks and service status information.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["core"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.

    Returns basic service status and availability information.
    """
    return {"status": "healthy", "service": "debug-env"}