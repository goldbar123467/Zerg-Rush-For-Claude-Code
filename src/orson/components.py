"""
Orson CLI - Rich visual components for the Zerg Swarm dashboard.

Renders buildings, workers, and status displays using Rich library.
Theme: Midwestern small town meets Starcraft Zerg.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel


# === Enums ===

class Building(Enum):
    """Buildings in Orson town."""
    TOWN_HALL = ("TOWN_HALL", "Overlord", None)
    SILO = ("SILO", "KERNEL", "K")
    LIBRARY = ("LIBRARY", "ML", "M")
    BANK = ("BANK", "QUANT", "Q")
    GAS_N_SIP = ("GAS_N_SIP", "DEX", "D")
    POST_OFFICE = ("POST_OFFICE", "INTEGRATION", "INT")
    CHURCH = ("CHURCH", None, None)
    CEMETERY = ("CEMETERY", None, None)
    MUSEUM = ("MUSEUM", None, None)  # Data vault
    NEWSPAPER = ("NEWSPAPER", None, None)  # Researcher
    SCHOOL = ("SCHOOL", None, None)  # Training center
    MCDONALDS = ("MCDONALDS", None, None)  # Quick tasks
    APARTMENTS = ("APARTMENTS", None, None)  # Agent pool


class TaskStatus(Enum):
    """Task completion status."""
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"


# === Dataclasses ===

@dataclass
class Worker:
    """A zergling worker assigned to a building."""
    id: str  # e.g., "K001", "M002"
    name: str  # e.g., "K001"
    task_id: Optional[str] = None
    registered_at: datetime = field(default_factory=datetime.now)
    ttl_minutes: float = 4.0  # 4-minute timebox

    @property
    def progress(self) -> float:
        """Calculate progress (0-1) based on time elapsed vs TTL."""
        elapsed = (datetime.now() - self.registered_at).total_seconds() / 60
        return min(1.0, elapsed / self.ttl_minutes)

    @property
    def time_remaining(self) -> float:
        """Time remaining in minutes."""
        elapsed = (datetime.now() - self.registered_at).total_seconds() / 60
        return max(0, self.ttl_minutes - elapsed)


@dataclass
class CompletedWorker:
    """A zergling that has finished its task."""
    id: str
    name: str
    task_id: str
    status: TaskStatus
    lines_written: int = 0
    message: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.now)


@dataclass
class DraftTask:
    """A task in the draft queue waiting to be assigned."""
    id: str
    lane: str
    task_type: str
    name: str
    file_path: str


@dataclass
class RadioEvent:
    """An event in the radio log."""
    timestamp: datetime
    worker_id: str
    worker_name: str
    task_id: Optional[str]
    message: str


# === Building Icons ===

BUILDING_ICONS = {
    "TOWN_HALL": ("town hall", "Overlord"),
    "SILO": ("silo", "KERNEL"),
    "LIBRARY": ("books", "ML"),
    "BANK": ("bank", "QUANT"),
    "GAS_N_SIP": ("fuelpump", "DEX"),
    "POST_OFFICE": ("postbox", "INTEGRATION"),
    "CHURCH": ("church", None),
    "CEMETERY": ("headstone", None),
}

# Unicode building icons
ICONS = {
    "TOWN_HALL": "\U0001f3db\ufe0f",   # Classical building
    "SILO": "\U0001f3ed",               # Factory
    "LIBRARY": "\U0001f4da",            # Books
    "BANK": "\U0001f3e6",               # Bank
    "GAS_N_SIP": "\u26fd",              # Fuel pump
    "POST_OFFICE": "\U0001f4ee",        # Postbox
    "CHURCH": "\u26ea",                 # Church
    "CEMETERY": "\U0001faa6",           # Headstone
    "MUSEUM": "\U0001f3db\ufe0f",       # Classical building (data vault)
    "NEWSPAPER": "\U0001f4f0",          # Newspaper (researcher)
    "SCHOOL": "\U0001f3eb",             # School building
    "MCDONALDS": "\U0001f35f",          # French fries
    "APARTMENTS": "\U0001f3e2",         # Office building (Agent Pool)
    "WORKER": "\U0001f477",             # Construction worker
    "DONE": "\u2705",                   # Green check
    "PARTIAL": "\u26a0\ufe0f",          # Warning
    "BLOCKED": "\U0001f6ab",            # No entry
    "FAILED": "\u274c",                 # Red X
}

LANE_ICONS = {
    "KERNEL": "\U0001f3ed",    # Factory/Silo
    "ML": "\U0001f4da",        # Books/Library
    "QUANT": "\U0001f3e6",     # Bank
    "DEX": "\u26fd",           # Fuel pump
    "INTEGRATION": "\U0001f4ee",  # Postbox
}


# === Progress Bar Rendering ===

def render_worker_bar(worker: Worker, width: int = 5) -> str:
    """
    Render a worker progress bar.

    Args:
        worker: Worker dataclass with progress info
        width: Width of progress bar in characters

    Returns:
        String like "K001" with progress bar using block chars
    """
    progress = worker.progress
    filled = int(progress * width)
    empty = width - filled

    # Use block characters: (empty) (filled)
    bar = "\u2591" * empty + "\u2593" * filled

    return f"{ICONS['WORKER']} {worker.name} {bar}"


def render_building(
    name: str,
    icon: str,
    lane: Optional[str],
    workers: List[Worker],
    width: int = 14
) -> Text:
    """
    Render a building with its workers.

    Args:
        name: Building name (e.g., "SILO", "LIBRARY")
        icon: Building icon emoji
        lane: Lane name (e.g., "KERNEL", "ML") or None
        workers: List of workers at this building
        width: Width for alignment

    Returns:
        Rich Text object with styled building display
    """
    text = Text()

    # Header line: icon + name
    header = f"{icon} {name}"
    text.append(header.ljust(width), style="bold cyan")
    text.append("\n")

    # Separator
    separator = "\u2500" * (width - 1)
    text.append(separator, style="dim")
    text.append("\n")

    # Lane name (if applicable)
    if lane:
        text.append(lane.ljust(width), style="yellow")
        text.append("\n")

    # Workers
    for worker in workers:
        bar = render_worker_bar(worker)
        text.append(bar, style="white")
        text.append("\n")

    return text


def render_buildings_row(buildings_data: List[dict], console_width: int = 80) -> Table:
    """
    Render a row of buildings side by side.

    Args:
        buildings_data: List of dicts with 'name', 'icon', 'lane', 'workers'
        console_width: Total width available

    Returns:
        Rich Table with buildings in columns
    """
    table = Table(
        show_header=False,
        show_edge=False,
        box=None,
        padding=(0, 1),
        expand=False
    )

    # Add columns - wider to accommodate emoji + progress bar
    for _ in buildings_data:
        table.add_column(width=16, no_wrap=True)

    # Build each building's text
    headers = []
    separators = []
    lanes = []
    worker_rows = []

    max_workers = max((len(b.get('workers', [])) for b in buildings_data), default=0)

    for b in buildings_data:
        icon = b.get('icon', '')
        name = b.get('name', '')
        headers.append(f"{icon} {name}")
        separators.append("\u2500" * 11)
        lanes.append(b.get('lane', '') or '')

    # Add header row
    table.add_row(*[Text(h, style="bold cyan") for h in headers])

    # Add separator row
    table.add_row(*[Text(s, style="dim") for s in separators])

    # Add lane row
    table.add_row(*[Text(l, style="yellow") for l in lanes])

    # Add worker rows
    for i in range(max_workers):
        row = []
        for b in buildings_data:
            workers = b.get('workers', [])
            if i < len(workers):
                bar = render_worker_bar(workers[i])
                row.append(Text(bar))
            else:
                row.append(Text(""))
        table.add_row(*row)

    return table


def render_cemetery_row(completed: List[CompletedWorker]) -> Table:
    """
    Render the cemetery with tombstones for completed workers.

    Args:
        completed: List of completed workers

    Returns:
        Rich Table showing tombstones with status
    """
    table = Table(
        title=f"{ICONS['CEMETERY']} CEMETERY",
        title_style="bold white",
        show_header=False,
        box=None,
        padding=(0, 1),
        expand=True
    )

    # Calculate columns based on number of completed workers
    num_cols = min(5, len(completed)) or 1
    for _ in range(num_cols):
        table.add_column(width=20)

    # Build tombstone entries
    tombstones = []
    for worker in completed:
        status_icon = ICONS.get(worker.status.value, ICONS['DONE'])

        if worker.status == TaskStatus.DONE:
            status_text = f"+{worker.lines_written} lines" if worker.lines_written else "DONE"
        elif worker.status == TaskStatus.PARTIAL:
            status_text = "PARTIAL"
        elif worker.status == TaskStatus.BLOCKED:
            status_text = "BLOCKED"
        else:
            status_text = worker.status.value

        tombstone = f"{ICONS['CEMETERY']} {worker.name}:{worker.task_id} {status_icon} {status_text}"
        tombstones.append(Text(tombstone, style="dim white"))

    # Fill rows
    for i in range(0, len(tombstones), num_cols):
        row = tombstones[i:i + num_cols]
        # Pad row if needed
        while len(row) < num_cols:
            row.append(Text(""))
        table.add_row(*row)

    return table


def render_draft_table(tasks: List[DraftTask]) -> Table:
    """
    Render the draft task queue.

    Args:
        tasks: List of draft tasks (max 5)

    Returns:
        Rich Table with numbered task list
    """
    table = Table(
        title="DRAFT QUEUE",
        title_style="bold magenta",
        show_header=True,
        header_style="bold",
        box=None,
        padding=(0, 1)
    )

    table.add_column("#", width=3, justify="right")
    table.add_column("", width=3)  # Lane icon
    table.add_column("Lane", width=12)
    table.add_column("Type", width=14)
    table.add_column("Name", width=15)
    table.add_column("File", style="dim")

    for i, task in enumerate(tasks[:5], 1):
        lane_icon = LANE_ICONS.get(task.lane, "")
        table.add_row(
            str(i),
            lane_icon,
            task.lane,
            task.task_type,
            task.name,
            task.file_path
        )

    return table


def render_radio_log(events: List[RadioEvent], max_lines: int = 6) -> Table:
    """
    Render the radio log with recent events.

    Args:
        events: List of radio events
        max_lines: Maximum number of lines to show

    Returns:
        Rich Table with timestamped event log
    """
    table = Table(
        title="RADIO LOG",
        title_style="bold green",
        show_header=True,
        header_style="bold dim",
        box=None,
        padding=(0, 1)
    )

    table.add_column("Time", width=8)
    table.add_column("Worker", width=12)
    table.add_column("Task", width=8)
    table.add_column("Message", style="white")

    # Show most recent events at bottom (take last max_lines)
    recent = events[-max_lines:] if len(events) > max_lines else events

    for event in recent:
        time_str = event.timestamp.strftime("%H:%M:%S")
        worker_display = f"{ICONS['WORKER']} {event.worker_name}"
        task_display = event.task_id or "-"

        table.add_row(
            Text(time_str, style="cyan"),
            Text(worker_display),
            Text(task_display, style="yellow"),
            Text(event.message)
        )

    return table


def render_church_animation(frame: int = 0) -> Text:
    """
    Render the church with walking animation.

    Args:
        frame: Animation frame number (0-3)

    Returns:
        Rich Text with animated worker
    """
    text = Text()

    # Header
    text.append(f"{ICONS['CHURCH']} CHURCH\n", style="bold cyan")
    text.append("\u2500" * 11 + "\n", style="dim")

    # Walking animation frames
    walk_frames = [
        f"  {ICONS['WORKER']}      ",
        f"    {ICONS['WORKER']}    ",
        f"      {ICONS['WORKER']}  ",
        f"        {ICONS['WORKER']}",
    ]

    frame_idx = frame % len(walk_frames)
    text.append(walk_frames[frame_idx], style="white")

    return text


def render_town_overview(
    wave: int,
    buildings: dict,
    completed: List[CompletedWorker],
    draft_tasks: List[DraftTask],
    radio_events: List[RadioEvent]
) -> Panel:
    """
    Render the complete town overview.

    Args:
        wave: Current wave number
        buildings: Dict mapping building name to worker list
        completed: List of completed workers
        draft_tasks: List of tasks in draft queue
        radio_events: List of radio log events

    Returns:
        Rich Panel containing the full dashboard
    """
    console = Console()

    # Build buildings data for the row
    buildings_config = [
        {"name": "TOWN HALL", "icon": ICONS["TOWN_HALL"], "lane": "Overlord",
         "workers": buildings.get("TOWN_HALL", [])},
        {"name": "SILO", "icon": ICONS["SILO"], "lane": "KERNEL",
         "workers": buildings.get("SILO", [])},
        {"name": "LIBRARY", "icon": ICONS["LIBRARY"], "lane": "ML",
         "workers": buildings.get("LIBRARY", [])},
        {"name": "BANK", "icon": ICONS["BANK"], "lane": "QUANT",
         "workers": buildings.get("BANK", [])},
        {"name": "GAS-N-SIP", "icon": ICONS["GAS_N_SIP"], "lane": "DEX",
         "workers": buildings.get("GAS_N_SIP", [])},
    ]

    buildings_table = render_buildings_row(buildings_config)

    return Panel(
        buildings_table,
        title=f"ORSON - Wave {wave}",
        title_align="center",
        subtitle="The hive wears flannel",
        subtitle_align="center",
        border_style="green"
    )


# === Convenience Functions ===

def create_worker(worker_id: str, task_id: Optional[str] = None) -> Worker:
    """Create a worker from an ID string."""
    return Worker(
        id=worker_id,
        name=worker_id,
        task_id=task_id,
        registered_at=datetime.now()
    )


def create_completed_worker(
    worker_id: str,
    task_id: str,
    status: str,
    lines_written: int = 0,
    message: Optional[str] = None
) -> CompletedWorker:
    """Create a completed worker record."""
    return CompletedWorker(
        id=worker_id,
        name=worker_id,
        task_id=task_id,
        status=TaskStatus(status) if isinstance(status, str) else status,
        lines_written=lines_written,
        message=message
    )


def create_draft_task(
    task_id: str,
    lane: str,
    task_type: str,
    name: str,
    file_path: str
) -> DraftTask:
    """Create a draft task."""
    return DraftTask(
        id=task_id,
        lane=lane,
        task_type=task_type,
        name=name,
        file_path=file_path
    )


def create_radio_event(
    worker_id: str,
    message: str,
    task_id: Optional[str] = None
) -> RadioEvent:
    """Create a radio event."""
    return RadioEvent(
        timestamp=datetime.now(),
        worker_id=worker_id,
        worker_name=worker_id,
        task_id=task_id,
        message=message
    )


# === Demo / Testing ===

def demo():
    """Demonstrate the components."""
    from rich.console import Console
    from datetime import timedelta

    console = Console()

    # Create sample workers with varying progress
    workers_silo = [
        Worker("K001", "K001", "K001", datetime.now() - timedelta(minutes=3)),
        Worker("K002", "K002", "K002", datetime.now() - timedelta(minutes=2)),
    ]
    workers_library = [
        Worker("M001", "M001", "M001", datetime.now() - timedelta(minutes=1)),
    ]
    workers_dex = [
        Worker("D001", "D001", "D001", datetime.now() - timedelta(minutes=3.5)),
        Worker("D002", "D002", "D002", datetime.now() - timedelta(minutes=1.5)),
    ]

    # Buildings data
    buildings = {
        "TOWN_HALL": [],
        "SILO": workers_silo,
        "LIBRARY": workers_library,
        "BANK": [],
        "GAS_N_SIP": workers_dex,
    }

    # Completed workers
    completed = [
        create_completed_worker("K003", "K003", "DONE", 45),
        create_completed_worker("M002", "M002", "PARTIAL", 23),
        create_completed_worker("D003", "D003", "BLOCKED", 0, "Missing dependency"),
    ]

    # Draft tasks
    drafts = [
        create_draft_task("K004", "KERNEL", "ADD_PURE_FN", "cuda_kernel", "src/kernel/ops.py"),
        create_draft_task("M003", "ML", "ADD_TEST", "test_model", "tests/test_model.py"),
        create_draft_task("Q001", "QUANT", "ADD_STUB", "backtest", "src/quant/bt.py"),
    ]

    # Radio events
    events = [
        create_radio_event("K001", "Starting task"),
        create_radio_event("M001", "Compiling..."),
        create_radio_event("D001", "TX built"),
        create_radio_event("K002", "Tests passing"),
        create_radio_event("D002", "Dry run OK"),
    ]

    # Render everything
    console.print("\n")
    console.print(render_town_overview(3, buildings, completed, drafts, events))
    console.print("\n")
    console.print(render_cemetery_row(completed))
    console.print("\n")
    console.print(render_draft_table(drafts))
    console.print("\n")
    console.print(render_radio_log(events))
    console.print("\n")
    console.print(render_church_animation(1))


if __name__ == "__main__":
    demo()
