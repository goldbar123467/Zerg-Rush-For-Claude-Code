"""Pydantic models for Zerg Swarm data structures."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SwarmState(BaseModel):
    """Current state of the swarm."""
    wave: int = 0
    active_zerglings: list[dict] = []
    completed_tasks: list[str] = []
    pending_tasks: list[str] = []
    last_updated: str = ""


class TaskCard(BaseModel):
    """Task card metadata."""
    task_id: str
    lane: str
    type: str
    status: str = "PENDING"
    objective: Optional[str] = None
    created: Optional[str] = None


class Zergling(BaseModel):
    """Active zergling worker."""
    name: str
    registered: str
    wave: int


class FileLock(BaseModel):
    """File lock record."""
    path: str
    holder: str
    acquired: str
    expires: str


class ToolResponse(BaseModel):
    """Standard tool response wrapper."""
    status: str = "ok"
    data: Optional[dict] = None
    error: Optional[str] = None
