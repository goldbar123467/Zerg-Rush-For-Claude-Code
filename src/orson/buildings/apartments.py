"""
Apartments Building - The Agent Pool

Tracks idle workers waiting for assignment.
"Every zergling needs a home between shifts."
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

APARTMENTS_ICON = "\U0001f3e2"  # Office building emoji


@dataclass
class IdleWorker:
    """A worker waiting in the pool."""
    name: str
    last_task: Optional[str] = None
    last_lane: Optional[str] = None
    idle_since: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0


@dataclass
class ApartmentsState:
    """State for the apartments building."""
    idle_workers: List[IdleWorker] = field(default_factory=list)
    capacity: int = 10  # Max workers in pool
    total_spawned: int = 0


def render_apartments(state: ApartmentsState) -> Panel:
    """Render the apartments panel showing idle workers."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", width=12)
    table.add_column("Last Task", width=10)
    table.add_column("Completed", width=8)
    table.add_column("Idle", width=8)

    for worker in state.idle_workers[:8]:
        idle_mins = (datetime.now() - worker.idle_since).seconds // 60
        table.add_row(
            worker.name,
            worker.last_task or "-",
            str(worker.tasks_completed),
            f"{idle_mins}m"
        )

    content = Text()
    content.append(f"Capacity: {len(state.idle_workers)}/{state.capacity}\n\n")

    return Panel(
        table,
        title=f"{APARTMENTS_ICON} APARTMENTS - Agent Pool",
        subtitle=f"{len(state.idle_workers)} idle",
        border_style="blue"
    )


def spawn_worker_from_pool(state: ApartmentsState) -> Optional[IdleWorker]:
    """Remove and return a worker from the pool."""
    if state.idle_workers:
        return state.idle_workers.pop(0)
    return None


def return_worker_to_pool(state: ApartmentsState, name: str, task_id: str, lane: str):
    """Return a completed worker to the pool."""
    # Find existing worker to increment tasks_completed
    existing_count = 0
    for w in state.idle_workers:
        if w.name == name:
            existing_count = w.tasks_completed

    worker = IdleWorker(
        name=name,
        last_task=task_id,
        last_lane=lane,
        tasks_completed=existing_count + 1
    )
    if len(state.idle_workers) < state.capacity:
        state.idle_workers.append(worker)
