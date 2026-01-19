"""
Orson State Management Module

Manages swarm state by reading from the SWARM directory.
Provides dataclass models and helper functions for state operations.

"In Orson, we know our neighbors. Even the ones with carapace."
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
import json
import random
import re

# Swarm root directory
SWARM_ROOT = Path("/home/ubuntu/projects/zerg-swarm/SWARM")

# Worker Time-To-Live (4 minutes as per zergling constraints)
WORKER_TTL_MINUTES = 4

# Midwestern worker names - the good folk of Orson
FIRST_NAMES = [
    "Earl", "Barb", "Jim", "Sue", "Dale", "Peggy", "Roy", "Deb",
    "Herb", "Marge", "Vern", "Dot", "Bud", "Fern", "Gene", "Opal",
    "Lyle", "Irma", "Glen", "Lois", "Arnie", "Wilma", "Chuck", "Betty",
    "Norm", "Edna", "Gus", "Mabel", "Floyd", "Vera", "Clem", "Ida",
    "Hank", "Pearl", "Clyde", "Doris", "Mel", "Gladys", "Ernie", "Hazel",
    "Walt", "Agnes", "Orville", "Mildred", "Leroy", "Elma", "Virgil", "Bonnie"
]

LAST_NAMES = [
    "Johnson", "Anderson", "Larson", "Peterson", "Olson", "Nelson",
    "Swenson", "Carlson", "Schmidt", "Mueller", "Hoffman", "Klein",
    "Weber", "Fischer", "Bauer", "Hartmann", "Kowalski", "Novak"
]


@dataclass
class Worker:
    """An active worker in the swarm (a zergling with a Midwestern name)."""
    name: str
    task_id: str
    lane: str
    registered: datetime
    wave: int
    status: str = "active"  # active, done, partial, blocked
    lines_written: int = 0


@dataclass
class CompletedWorker:
    """A worker that has finished their task and gone home for supper."""
    name: str
    task_id: str
    status: str  # done, partial, blocked
    lines: int
    timestamp: datetime
    memory_id: Optional[str] = None  # RAG memory ID from pre-spawn injection
    feedback_sent: bool = False  # Whether RAG feedback was sent


@dataclass
class DraftTask:
    """A task waiting in the drafts, not yet assigned."""
    lane: str
    task_type: str
    name: str
    file_path: str


@dataclass
class RadioEvent:
    """A message broadcast on the town radio (event log)."""
    timestamp: datetime
    worker: str
    task_id: str
    message: str
    icon: str = "radio"  # worker, check, alert, coffee, tools


@dataclass
class SwarmState:
    """The complete state of the Orson swarm."""
    wave: int = 0
    workers: List[Worker] = field(default_factory=list)
    completed: List[CompletedWorker] = field(default_factory=list)
    draft_tasks: List[DraftTask] = field(default_factory=list)
    events: List[RadioEvent] = field(default_factory=list)
    goal: str = ""
    last_updated: Optional[datetime] = None
    # MCP connection status
    mcp_connected: bool = False
    mcp_last_ping: Optional[datetime] = None
    # RAG Brain connection status
    rag_connected: bool = False
    rag_stats: dict = field(default_factory=dict)
    # Agent pool (apartments)
    idle_workers: List = field(default_factory=list)
    pool_capacity: int = 10


def generate_worker_name() -> str:
    """Generate a fun Midwestern worker name."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


def generate_short_name() -> str:
    """Generate just a first name for compact display."""
    return random.choice(FIRST_NAMES)


def get_state_path() -> Path:
    """Get the path to STATE.json."""
    return SWARM_ROOT / "STATE.json"


def load_state() -> SwarmState:
    """
    Load swarm state from SWARM/STATE.json.

    Returns a SwarmState object with workers mapped from active_zerglings.
    """
    state_path = get_state_path()

    if not state_path.exists():
        return SwarmState()

    try:
        with open(state_path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return SwarmState()

    # Parse active zerglings into Worker objects
    workers = []
    for z in data.get("active_zerglings", []):
        # Parse registration time
        registered = datetime.now()
        if "registered" in z:
            try:
                registered = datetime.fromisoformat(z["registered"])
            except (ValueError, TypeError):
                pass

        # Determine lane and task from name or pending tasks
        task_id = z.get("task_id", "")
        lane = z.get("lane", "")

        # Generate a friendly name if just an agent ID
        name = z.get("name", "Unknown")
        if name.startswith("claude-") or name.startswith("opencode-"):
            # Keep the technical name but could map to friendly name
            pass

        workers.append(Worker(
            name=name,
            task_id=task_id,
            lane=lane,
            registered=registered,
            wave=z.get("wave", 0),
            status=z.get("status", "active"),
            lines_written=z.get("lines_written", 0)
        ))

    # Parse completed tasks
    completed = []
    for task_id in data.get("completed_tasks", []):
        # Basic completion record
        completed.append(CompletedWorker(
            name="",  # Not tracked in current format
            task_id=task_id,
            status="done",
            lines=0,
            timestamp=datetime.now()
        ))

    # Parse pending tasks as draft tasks
    draft_tasks = []
    for task_ref in data.get("pending_tasks", []):
        # Parse lane/task format like "KERNEL/K001"
        parts = task_ref.split("/")
        if len(parts) == 2:
            lane, task_name = parts
            draft_tasks.append(DraftTask(
                lane=lane,
                task_type="TASK",
                name=task_name,
                file_path=f"TASKS/{lane}/{task_name}.md"
            ))

    # Parse last_updated
    last_updated = None
    if "last_updated" in data:
        try:
            last_updated = datetime.fromisoformat(data["last_updated"])
        except (ValueError, TypeError):
            pass

    return SwarmState(
        wave=data.get("wave", 0),
        workers=workers,
        completed=completed,
        draft_tasks=draft_tasks,
        events=[],  # Events are not persisted in STATE.json
        goal=data.get("goal", ""),
        last_updated=last_updated
    )


def save_state(state: SwarmState) -> None:
    """
    Save swarm state to SWARM/STATE.json.

    Uses atomic write pattern to prevent corruption.
    """
    state_path = get_state_path()

    # Convert workers back to active_zerglings format
    active_zerglings = []
    for w in state.workers:
        active_zerglings.append({
            "name": w.name,
            "registered": w.registered.isoformat(),
            "wave": w.wave,
            "task_id": w.task_id,
            "lane": w.lane,
            "status": w.status,
            "lines_written": w.lines_written
        })

    # Convert completed workers to completed_tasks
    completed_tasks = [c.task_id for c in state.completed]

    # Convert draft tasks to pending_tasks
    pending_tasks = [f"{d.lane}/{d.name}" for d in state.draft_tasks]

    data = {
        "wave": state.wave,
        "active_zerglings": active_zerglings,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "goal": state.goal,
        "last_updated": datetime.now().isoformat()
    }

    # Atomic write
    temp_path = state_path.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=2)
    temp_path.rename(state_path)


def refresh_state(state: SwarmState) -> SwarmState:
    """
    Refresh state by re-reading from files.

    Updates:
    - Worker list from STATE.json
    - Draft tasks from TASKS directories
    - Completed from INBOX
    """
    # Reload base state
    fresh = load_state()

    # Preserve events from current state (they're session-local)
    fresh.events = state.events

    # Scan INBOX for new results
    inbox_dir = SWARM_ROOT / "INBOX"
    if inbox_dir.exists():
        for result_file in inbox_dir.glob("*_RESULT.md"):
            task_id = result_file.stem.replace("_RESULT", "")

            # Check if already in completed
            if not any(c.task_id == task_id for c in fresh.completed):
                # Parse result file for details
                status, lines, worker = parse_result_file(result_file)
                fresh.completed.append(CompletedWorker(
                    name=worker,
                    task_id=task_id,
                    status=status,
                    lines=lines,
                    timestamp=datetime.fromtimestamp(result_file.stat().st_mtime)
                ))

    # Scan TASKS directories for pending tasks not in state
    tasks_dir = SWARM_ROOT / "TASKS"
    if tasks_dir.exists():
        for lane_dir in tasks_dir.iterdir():
            if lane_dir.is_dir() and lane_dir.name not in [".", ".."]:
                lane = lane_dir.name
                for task_file in lane_dir.glob("*.md"):
                    if task_file.name == "README.md":
                        continue
                    task_name = task_file.stem
                    # Check if already tracked
                    if not any(d.name == task_name for d in fresh.draft_tasks):
                        if not any(c.task_id == task_name for c in fresh.completed):
                            task_type = parse_task_type(task_file)
                            fresh.draft_tasks.append(DraftTask(
                                lane=lane,
                                task_type=task_type,
                                name=task_name,
                                file_path=f"TASKS/{lane}/{task_name}.md"
                            ))

    return fresh


def parse_result_file(file_path: Path) -> Tuple[str, int, str]:
    """
    Parse a result file to extract status, lines, and worker name.

    Returns: (status, lines, worker_name)
    """
    status = "done"
    lines = 0
    worker = ""

    try:
        content = file_path.read_text()

        # Look for status in metadata table
        status_match = re.search(r'\|\s*Status\s*\|\s*(\w+)', content, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).lower()

        # Look for zergling/worker name
        worker_match = re.search(r'\|\s*Zergling\s*\|\s*([^|]+)\s*\|', content, re.IGNORECASE)
        if worker_match:
            worker = worker_match.group(1).strip()

        # Count lines in Files Modified section
        lines_match = re.search(r'(\d+)\s*lines?\s*added', content, re.IGNORECASE)
        if lines_match:
            lines = int(lines_match.group(1))

    except IOError:
        pass

    return status, lines, worker


def parse_task_type(file_path: Path) -> str:
    """Parse task type from a task file."""
    try:
        content = file_path.read_text()
        type_match = re.search(r'Type:\s*(\w+)', content, re.IGNORECASE)
        if type_match:
            return type_match.group(1)
        type_match = re.search(r'\|\s*Type\s*\|\s*([^|]+)\s*\|', content)
        if type_match:
            return type_match.group(1).strip()
    except IOError:
        pass
    return "TASK"


def add_event(
    state: SwarmState,
    worker: str,
    task_id: str,
    message: str,
    icon: str = "radio"
) -> None:
    """
    Add an event to the radio log.

    Icons: worker, check, alert, coffee, tools, radio
    """
    event = RadioEvent(
        timestamp=datetime.now(),
        worker=worker,
        task_id=task_id,
        message=message,
        icon=icon
    )
    state.events.append(event)

    # Keep only last 100 events
    if len(state.events) > 100:
        state.events = state.events[-100:]


def get_worker_progress(worker: Worker) -> float:
    """
    Calculate worker progress as 0-1 based on 4-min TTL.

    Returns 1.0 if worker has exceeded TTL.
    """
    elapsed = datetime.now() - worker.registered
    ttl = timedelta(minutes=WORKER_TTL_MINUTES)

    progress = elapsed.total_seconds() / ttl.total_seconds()
    return min(1.0, max(0.0, progress))


def get_worker_time_remaining(worker: Worker) -> timedelta:
    """Get remaining time for a worker before TTL expires."""
    elapsed = datetime.now() - worker.registered
    ttl = timedelta(minutes=WORKER_TTL_MINUTES)
    remaining = ttl - elapsed

    if remaining.total_seconds() < 0:
        return timedelta(0)
    return remaining


def is_worker_expired(worker: Worker) -> bool:
    """Check if a worker has exceeded their TTL."""
    return get_worker_progress(worker) >= 1.0


def increment_wave(state: SwarmState) -> SwarmState:
    """
    Increment the wave counter.

    Also adds an event to the radio log.
    """
    old_wave = state.wave
    state.wave += 1

    add_event(
        state,
        worker="Overlord",
        task_id="",
        message=f"Wave {old_wave} complete. Starting wave {state.wave}.",
        icon="radio"
    )

    return state


def collect_results(state: SwarmState) -> SwarmState:
    """
    Collect results from INBOX and update state.

    Moves completed tasks from workers to completed list.
    Archives result files.
    """
    inbox_dir = SWARM_ROOT / "INBOX"
    archive_dir = SWARM_ROOT / "ARCHIVE"

    if not inbox_dir.exists():
        return state

    collected = 0
    for result_file in inbox_dir.glob("*_RESULT.md"):
        task_id = result_file.stem.replace("_RESULT", "")

        # Skip if already processed
        if any(c.task_id == task_id for c in state.completed):
            continue

        # Parse the result
        status, lines, worker = parse_result_file(result_file)

        # Add to completed
        state.completed.append(CompletedWorker(
            name=worker or generate_short_name(),
            task_id=task_id,
            status=status,
            lines=lines,
            timestamp=datetime.fromtimestamp(result_file.stat().st_mtime)
        ))

        # Remove from workers if present
        state.workers = [w for w in state.workers if w.task_id != task_id]

        # Remove from draft tasks if present
        state.draft_tasks = [d for d in state.draft_tasks if d.name != task_id]

        # Archive the result file
        if archive_dir.exists():
            archive_path = archive_dir / result_file.name
            try:
                result_file.rename(archive_path)
            except OSError:
                pass  # Leave in inbox if archive fails

        collected += 1

        # Add event
        add_event(
            state,
            worker=worker or task_id,
            task_id=task_id,
            message=f"Task {task_id} completed ({status}). {lines} lines written.",
            icon="check" if status == "done" else "alert"
        )

    if collected > 0:
        add_event(
            state,
            worker="Overlord",
            task_id="",
            message=f"Collected {collected} results from the inbox.",
            icon="coffee"
        )

    return state


def get_active_lanes(state: SwarmState) -> List[str]:
    """Get list of lanes with active workers."""
    return list(set(w.lane for w in state.workers if w.lane))


def get_pending_by_lane(state: SwarmState) -> dict:
    """Get pending tasks grouped by lane."""
    by_lane = {}
    for task in state.draft_tasks:
        if task.lane not in by_lane:
            by_lane[task.lane] = []
        by_lane[task.lane].append(task)
    return by_lane


def get_summary(state: SwarmState) -> dict:
    """Get a summary of current swarm state."""
    return {
        "wave": state.wave,
        "active_workers": len(state.workers),
        "completed_tasks": len(state.completed),
        "pending_tasks": len(state.draft_tasks),
        "active_lanes": get_active_lanes(state),
        "recent_events": len(state.events),
        "goal": state.goal,
        "idle_workers": len(state.idle_workers)
    }


def worker_to_pool(state: SwarmState, worker_name: str, task_id: str, lane: str):
    """Move completed worker to idle pool instead of directly to cemetery."""
    idle = {
        "name": worker_name,
        "last_task": task_id,
        "last_lane": lane,
        "idle_since": datetime.now().isoformat()
    }
    if len(state.idle_workers) < state.pool_capacity:
        state.idle_workers.append(idle)


def worker_from_pool(state: SwarmState) -> Optional[dict]:
    """Get an idle worker from the pool."""
    if state.idle_workers:
        return state.idle_workers.pop(0)
    return None


# === RAG Feedback Loop Functions ===

async def send_worker_feedback(completed: CompletedWorker, rag_client) -> bool:
    """
    Send RAG feedback based on worker completion status.

    DONE → helpful=True (positive feedback)
    PARTIAL/BLOCKED → helpful=False (negative feedback)

    Args:
        completed: The completed worker
        rag_client: RAG client with feedback() method

    Returns:
        True if feedback was sent successfully
    """
    if not rag_client or not completed.memory_id:
        return False

    if completed.feedback_sent:
        return True  # Already sent

    # Determine helpfulness based on status
    helpful = completed.status.lower() == "done"

    try:
        result = await rag_client.feedback(completed.memory_id, helpful=helpful)
        if result:
            completed.feedback_sent = True
            return True
    except Exception:
        pass

    return False


async def store_wave_outcome(
    wave_num: int,
    completed_workers: List[CompletedWorker],
    rag_client
) -> Optional[str]:
    """
    Store wave outcome as a memory for future learning.

    Args:
        wave_num: Wave number
        completed_workers: List of workers completed in this wave
        rag_client: RAG client with remember() method

    Returns:
        Memory ID if stored successfully
    """
    if not rag_client:
        return None

    # Filter workers from this wave (by timestamp proximity or explicit tracking)
    wave_workers = completed_workers  # In practice, filter by wave

    done_count = sum(1 for w in wave_workers if w.status.lower() == "done")
    partial_count = sum(1 for w in wave_workers if w.status.lower() == "partial")
    blocked_count = sum(1 for w in wave_workers if w.status.lower() == "blocked")
    total = len(wave_workers)
    total_lines = sum(w.lines for w in wave_workers)

    # Build task summary
    task_ids = [w.task_id for w in wave_workers[:5]]
    task_summary = ", ".join(task_ids)
    if len(wave_workers) > 5:
        task_summary += f" (+{len(wave_workers) - 5} more)"

    # Create outcome content
    success_rate = (done_count / total * 100) if total > 0 else 0
    outcome = (
        f"Wave {wave_num}: {done_count}/{total} success ({success_rate:.0f}%). "
        f"Partial: {partial_count}, Blocked: {blocked_count}. "
        f"Lines written: {total_lines}. Tasks: {task_summary}"
    )

    try:
        result = await rag_client.remember(
            outcome,
            category="outcome",
            tags=["wave", f"wave-{wave_num}", "swarm-outcome"]
        )
        if result and isinstance(result, dict):
            return result.get("id", result.get("memory_id"))
    except Exception:
        pass

    return None


async def process_cemetery_feedback(
    state: SwarmState,
    rag_client,
    max_pending: int = 10
) -> int:
    """
    Process pending feedback for completed workers in cemetery.

    Args:
        state: SwarmState with completed workers
        rag_client: RAG client
        max_pending: Maximum workers to process per call

    Returns:
        Number of feedback items sent
    """
    sent = 0
    pending = [w for w in state.completed if w.memory_id and not w.feedback_sent]

    for worker in pending[:max_pending]:
        if await send_worker_feedback(worker, rag_client):
            sent += 1

    return sent


def get_wave_stats(state: SwarmState, wave_num: int = None) -> dict:
    """
    Get statistics for a wave (or current wave).

    Returns dict with done, partial, blocked counts and success rate.
    """
    workers = state.completed
    if wave_num is not None:
        # Filter by wave if tracking is available
        pass

    done = sum(1 for w in workers if w.status.lower() == "done")
    partial = sum(1 for w in workers if w.status.lower() == "partial")
    blocked = sum(1 for w in workers if w.status.lower() == "blocked")
    total = len(workers)

    return {
        "done": done,
        "partial": partial,
        "blocked": blocked,
        "total": total,
        "success_rate": (done / total * 100) if total > 0 else 0,
        "total_lines": sum(w.lines for w in workers)
    }


# === Cemetery & Epitaphs ===

@dataclass
class Tombstone:
    """A tombstone in the cemetery for a worker who has completed their task."""
    worker_name: str
    task_id: str
    status: str  # DONE, PARTIAL, BLOCKED, TIMEOUT, FAILED
    wave: int
    lines_written: int
    epitaph: str
    timestamp: datetime = field(default_factory=datetime.now)
    memory_id: Optional[str] = None  # RAG memory ID if knowledge was injected


# Epitaphs for workers based on their completion status - Midwestern wisdom
EPITAPHS = {
    "DONE": [
        "Served well",
        "Did the job right",
        "A good day's work",
        "That oughta do it",
        "Left it better than he found it",
        "The neighbors would be proud",
        "Good enough for the county fair",
        "Earned his supper tonight",
    ],
    "PARTIAL": [
        "Gave what he could",
        "Ran outta time",
        "Almost had it",
        "Tried his best",
        "Got halfway there",
        "Did what he could with what he had",
        "The spirit was willing",
        "Close but no cigar",
    ],
    "BLOCKED": [
        "Needed more context",
        "Couldn't find the way",
        "Waited for help that never came",
        "Dependencies unclear",
        "Hit a wall and sat down",
        "Asked a question nobody answered",
        "Wrong tool for the job",
        "Sometimes you just can't",
    ],
    "TIMEOUT": [
        "Time waits for no one",
        "Dragged away mid-thought",
        "The clock ran out",
        "Gone too soon",
        "Supper bell rang early",
        "Had to get home before dark",
        "The whistle blew",
        "Shift ended, work didn't",
    ],
    "FAILED": [
        "It happens to the best of us",
        "Gave it his all",
        "Not every seed grows",
        "Even good folk stumble",
        "Tomorrow is another day",
        "Can't win 'em all",
        "The road had other plans",
        "Sometimes the tractor just won't start",
    ],
    "UNKNOWN": [
        "Rest in peace",
        "We'll never know",
        "Gone but not forgotten",
        "A mystery to the end",
    ],
}


def get_epitaph(status: str) -> str:
    """
    Get a random epitaph for a worker based on their completion status.

    Args:
        status: Worker status (DONE, PARTIAL, BLOCKED, TIMEOUT, FAILED)

    Returns:
        A Midwestern-flavored epitaph string
    """
    status_upper = status.upper()
    epitaphs = EPITAPHS.get(status_upper, EPITAPHS["UNKNOWN"])
    return random.choice(epitaphs)


def count_lines_in_output(output: str) -> int:
    """
    Count lines written from worker output.

    Looks for patterns like "| Lines | 42 |" or "Lines: 42"

    Args:
        output: Worker output text

    Returns:
        Number of lines written, or 0 if not found
    """
    import re

    # Pattern: "| Lines | 42 |"
    match = re.search(r'\|\s*Lines\s*\|\s*(\d+)\s*\|', output)
    if match:
        return int(match.group(1))

    # Pattern: "Lines: 42"
    match = re.search(r'Lines:\s*(\d+)', output)
    if match:
        return int(match.group(1))

    # Pattern: "42 lines added" or "42 lines written"
    match = re.search(r'(\d+)\s*lines?\s*(?:added|written)', output, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern: "Added 42 lines" or "Wrote 42 lines"
    match = re.search(r'(?:added|wrote)\s*(\d+)\s*lines?', output, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return 0
