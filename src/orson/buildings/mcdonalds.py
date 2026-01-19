"""
McDonald's Building - Quick Tasks

Fast food for fast tasks. Bypass the wave system.
"Over 1 billion tasks served."
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

MCDONALDS_ICON = "\U0001f35f"  # French fries emoji


@dataclass
class QuickTask:
    """A quick task bypassing wave system."""
    description: str
    lane: str
    file_path: str
    created: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, running, done, failed
    result: Optional[str] = None


@dataclass
class McDonaldsState:
    """State for quick task queue."""
    queue: List[QuickTask] = field(default_factory=list)
    history: List[QuickTask] = field(default_factory=list)
    is_visible: bool = False
    input_mode: bool = False
    current_input: str = ""


def render_mcdonalds(state: McDonaldsState) -> Panel:
    """Render McDonald's quick task panel."""
    content = Text()

    content.append("\U0001f354 QUICK TASK MENU\n\n", style="bold yellow")
    content.append("Press 'f' for Fast Task (no wave)\n", style="dim")
    content.append("Press 'enter' to execute\n\n", style="dim")

    if state.queue:
        content.append("\U0001f4cb QUEUE:\n", style="cyan")
        for i, task in enumerate(state.queue[:5], 1):
            status_icon = {
                "pending": "\u23f3",
                "running": "\U0001f504",
                "done": "\u2705",
                "failed": "\u274c"
            }.get(task.status, "?")
            content.append(f"  {i}. {status_icon} ", style="white")
            content.append(f"{task.description[:30]}\n", style="dim")

    if state.history:
        content.append("\n\U0001f4dc RECENT:\n", style="green")
        for task in state.history[-3:]:
            content.append(f"  \u2705 {task.description[:30]}\n", style="dim")

    return Panel(
        content,
        title=f"{MCDONALDS_ICON} McDONALD'S - Quick Tasks",
        subtitle="Over 1B served",
        border_style="red"
    )


def create_quick_task(description: str, lane: str, file_path: str) -> QuickTask:
    """Create a new quick task."""
    return QuickTask(
        description=description,
        lane=lane,
        file_path=file_path
    )


async def execute_quick_task(task: QuickTask, mcp_client) -> bool:
    """Execute a quick task via direct MCP call."""
    # This would call mcp_client.send_command with task params
    # Bypasses wave system entirely
    task.status = "running"
    # ... execute ...
    task.status = "done"
    return True
