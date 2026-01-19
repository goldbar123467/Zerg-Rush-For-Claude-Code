"""
Orson CLI - Terminal UI for Zerg Swarm Management

Main entry point with Rich Live display and keyboard input handling.
Theme: Midwestern small town meets Starcraft Zerg.
"""

import asyncio
import atexit
import json
import os
import queue
import signal
import sys
import select
import termios
import tty
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field

from .mcp_client import MCPClient, get_client
from .rag_client import RAGClient, get_rag_client
from .spawner import (
    SpawnerState, SpawnedWorker, get_spawner_state, spawn_wave, collect_completed,
    check_tmux_available, check_claude_available, kill_all_workers, get_worker_output
)
from .buildings.museum import MuseumState, render_museum, load_museum_data, refresh_museum_concepts, load_concept_memories
from .buildings.apartments import ApartmentsState, IdleWorker, spawn_worker_from_pool, return_worker_to_pool
from .buildings.newspaper import (
    NewspaperState, render_newspaper, scan_for_changes, queue_for_research,
    store_to_rag, process_queue, init_default_watches, RAGFinding
)
from .rag_client import chunk_file, format_quality_display
from .buildings.school import SchoolState, render_school, load_prompts, refresh_school_knowledge, fetch_lane_knowledge_sync
from .buildings.mcdonalds import McDonaldsState, render_mcdonalds
from .buildings.brain import BrainPanelState, render_brain_panel, render_brain_status_indicator
from .buildings.daemons import DaemonConfig, DaemonPanelState, render_daemons_panel, get_daemon_summary
from .refresh_controller import RefreshController
from .status_manager import StatusMessageManager
from .state import (
    send_worker_feedback, store_wave_outcome, process_cemetery_feedback, get_wave_stats,
    Tombstone, get_epitaph, count_lines_in_output, CompletedWorker
)
from .daemons.researcher import ResearcherDaemon
from .daemons.teacher import TeacherDaemon

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style


# === Paths ===
ORSON_ROOT = Path(__file__).parent
PROJECT_ROOT = ORSON_ROOT.parent.parent  # src/orson -> src -> zerg-swarm
SWARM_ROOT = PROJECT_ROOT / "SWARM"
STATE_FILE = SWARM_ROOT / "STATE.json"
TASKS_DIR = SWARM_ROOT / "TASKS"
INBOX_DIR = SWARM_ROOT / "INBOX"
OUTBOX_DIR = SWARM_ROOT / "OUTBOX"

# Lanes in the swarm
LANES = ["KERNEL", "ML", "QUANT", "DEX", "INTEGRATION"]


# === State Management ===
@dataclass
class SwarmState:
    """Current swarm state for the TUI."""
    wave: int = 0
    active_zerglings: list = field(default_factory=list)
    completed_tasks: list = field(default_factory=list)
    pending_tasks: list = field(default_factory=list)
    last_updated: str = ""
    selected_building: int = 1
    selected_task: Optional[str] = None
    status_message: str = ""  # DEPRECATED: Use status_manager instead (Wave 27)
    tasks_by_lane: dict = field(default_factory=dict)
    inbox_results: list = field(default_factory=list)
    # MCP connection status
    mcp_connected: bool = False
    mcp_last_ping: Optional[datetime] = None
    # Wave spawn confirmation state (Wave 5)
    spawn_confirm_pending: bool = False
    # Decompose mode state (Wave 7)
    decompose_mode: bool = False
    decompose_goal: str = ""
    draft_tasks: list = field(default_factory=list)
    # Museum state (Wave 8)
    museum_visible: bool = False
    museum_state: MuseumState = field(default_factory=MuseumState)
    # Newspaper state (Wave 12)
    newspaper_visible: bool = False
    newspaper_state: NewspaperState = field(default_factory=NewspaperState)
    # School state (Wave 10)
    school_visible: bool = False
    school_state: SchoolState = field(default_factory=SchoolState)
    # McDonald's state (Wave 11)
    mcdonalds_visible: bool = False
    mcdonalds_state: McDonaldsState = field(default_factory=McDonaldsState)
    # Brain panel state (Wave 14)
    brain_visible: bool = False
    brain_state: BrainPanelState = field(default_factory=BrainPanelState)
    # RAG connection status
    rag_connected: bool = False
    # Daemon status indicators
    researcher_active: bool = False  # Newspaper file watcher
    teacher_active: bool = False     # School knowledge injector
    # Real spawner state
    spawner_state: SpawnerState = field(default_factory=SpawnerState)
    real_spawn_enabled: bool = True  # Enable real tmux spawning
    tmux_available: bool = False
    claude_available: bool = False
    # Researcher daemon reference
    researcher_daemon: Optional[ResearcherDaemon] = None
    # Teacher daemon reference
    teacher_daemon: Optional[TeacherDaemon] = None
    # Apartments (worker pool)
    apartments_state: ApartmentsState = field(default_factory=ApartmentsState)
    # Radio events (spawn messages)
    radio_events: list = field(default_factory=list)
    # Completed workers (for cemetery feedback)
    completed_workers: list = field(default_factory=list)
    # Cemetery (tombstones for departed workers)
    cemetery: list = field(default_factory=list)
    # Daemon control panel (Wave 26)
    daemons_visible: bool = False
    daemons_state: DaemonPanelState = field(default_factory=DaemonPanelState)
    daemon_config: DaemonConfig = field(default_factory=DaemonConfig)
    # Refresh controller (Wave 27)
    refresh_controller: RefreshController = field(default_factory=RefreshController)
    # Status message manager (Wave 27.4)
    status_manager: StatusMessageManager = field(default_factory=StatusMessageManager)
    # Thread-safe event queue for async callbacks
    _event_queue: queue.Queue = field(default_factory=lambda: queue.Queue(maxsize=100))


# === Constants ===
MAX_RADIO_EVENTS = 50
MAX_COMPLETED_WORKERS = 100
MAX_DECOMPOSE_GOAL_LENGTH = 500


# === Radio Events ===

def add_radio_event(state: SwarmState, message: str, icon: str = "\U0001f4fb"):
    """Add a radio event to the state.

    Args:
        state: SwarmState to update
        message: Event message
        icon: Emoji icon for the event
    """
    event = {
        "timestamp": datetime.now(),
        "message": message,
        "icon": icon
    }
    state.radio_events.append(event)
    # Keep only last MAX_RADIO_EVENTS events
    if len(state.radio_events) > MAX_RADIO_EVENTS:
        state.radio_events = state.radio_events[-MAX_RADIO_EVENTS:]

def add_radio_event_async(state: SwarmState, message: str, icon: str = "\U0001f4fb"):
    """Thread-safe event addition for async callbacks."""
    try:
        state._event_queue.put_nowait({
            "timestamp": datetime.now(),
            "message": message,
            "icon": icon
        })
    except queue.Full:
        pass  # Drop if queue full

def flush_event_queue(state: SwarmState) -> None:
    """Flush pending events from queue to radio_events list. Call from main loop."""
    while True:
        try:
            event = state._event_queue.get_nowait()
            state.radio_events.append(event)
        except queue.Empty:
            break
    # Trim to max
    if len(state.radio_events) > MAX_RADIO_EVENTS:
        state.radio_events = state.radio_events[-MAX_RADIO_EVENTS:]


def init_worker_pool(state: SwarmState, count: int = 10) -> SwarmState:
    """Initialize the worker pool with idle workers.

    Args:
        state: SwarmState to update
        count: Number of workers to create

    Returns:
        Updated state
    """
    from .state import FIRST_NAMES
    import random

    for _ in range(count):
        if len(state.apartments_state.idle_workers) >= state.apartments_state.capacity:
            break
        name = random.choice(FIRST_NAMES)
        # Ensure unique names
        existing = [w.name for w in state.apartments_state.idle_workers]
        while name in existing:
            name = random.choice(FIRST_NAMES)
        state.apartments_state.idle_workers.append(IdleWorker(name=name))

    return state


# === Worker Monitor ===

def handle_worker_death(
    state: SwarmState,
    worker: SpawnedWorker,
    status: str,
    message: str,
    lines_written: int = 0
) -> SwarmState:
    """Handle a worker completing or timing out.

    Full death flow:
    1. Log status to radio
    2. Church animation (walking to church)
    3. Add tombstone to cemetery
    4. Send RAG feedback if applicable
    5. Return worker to pool (reincarnation)

    Args:
        state: SwarmState to update
        worker: The worker that died
        status: Final status (DONE, PARTIAL, BLOCKED, TIMEOUT, FAILED)
        message: Status message from output
        lines_written: Number of lines written by worker

    Returns:
        Updated state
    """
    # Update worker status
    worker.status = status.lower()

    # Add to spawner's completed workers
    state.spawner_state.completed_workers.append(worker)

    # Determine icon based on status
    status_icons = {
        "DONE": "\u2705",        # Green check ✅
        "PARTIAL": "\u26a0\ufe0f",  # Warning ⚠️
        "BLOCKED": "\U0001f6ab",  # No entry 🚫
        "TIMEOUT": "\u23f1\ufe0f",  # Stopwatch ⏱️
        "FAILED": "\u274c",       # Red X ❌
        "UNKNOWN": "\u2753"       # Question mark ❓
    }
    icon = status_icons.get(status.upper(), "\U0001f4fb")

    # 1. Log status to radio
    add_radio_event(
        state,
        f"{icon} {worker.name} \u2502 {worker.task_id} \u2502 {status}",
        icon
    )

    # 2. Church animation
    add_radio_event(
        state,
        f"\U0001f47b {worker.name} walking to church...",
        "\u26ea"  # Church ⛪
    )

    # 3. Create tombstone and add to cemetery
    epitaph = get_epitaph(status)
    tombstone = Tombstone(
        worker_name=worker.name,
        task_id=worker.task_id,
        status=status,
        wave=state.wave,
        lines_written=lines_written,
        epitaph=epitaph,
        timestamp=datetime.now(),
        memory_id=worker.injected_knowledge if hasattr(worker, 'injected_knowledge') else None
    )
    state.cemetery.append(tombstone)

    # Cemetery radio message
    add_radio_event(
        state,
        f"\U0001faa6 {worker.name} \u2502 \"{epitaph}\"",
        "\U0001faa6"  # Headstone 🪦
    )

    # 4. Create CompletedWorker for RAG feedback tracking
    completed = CompletedWorker(
        name=worker.name,
        task_id=worker.task_id,
        status=status,
        lines=lines_written,
        timestamp=datetime.now(),
        memory_id=worker.injected_knowledge if hasattr(worker, 'injected_knowledge') else None,
        feedback_sent=False
    )
    state.completed_workers.append(completed)
    # Cleanup old completed workers
    if len(state.completed_workers) > MAX_COMPLETED_WORKERS:
        state.completed_workers = state.completed_workers[-MAX_COMPLETED_WORKERS:]

    # Send RAG feedback if connected and memory was used
    if state.rag_connected and completed.memory_id:
        try:
            rag_client = get_rag_client()
            loop = asyncio.get_event_loop()
            helpful = status.upper() == "DONE"
            loop.run_until_complete(rag_client.feedback(completed.memory_id, helpful))
            completed.feedback_sent = True
        except Exception:
            pass  # Feedback is best-effort

    # Update task status in tasks_by_lane
    for task in state.tasks_by_lane.get(worker.lane, []):
        if task["id"] == worker.task_id:
            task["status"] = status
            break

    # 5. Return worker to pool (reincarnation) if they completed
    if status.upper() in ("DONE", "PARTIAL"):
        # Worker goes back to apartments for next assignment
        state.apartments_state.idle_workers.append(IdleWorker(name=worker.name))

    return state


async def monitor_workers_async(state: SwarmState) -> None:
    """Background coroutine to monitor active workers.

    Checks all active workers every second for:
    - TTL expiration (kills and marks as TIMEOUT)
    - Session completion (parses output for status)

    Args:
        state: SwarmState to monitor and update
    """
    from .spawner import (
        get_worker_output, parse_worker_result, cleanup_worker_session,
        get_active_tmux_sessions, kill_tmux_session
    )

    while state.spawner_state.active_workers:
        workers_to_remove = []

        for worker in state.spawner_state.active_workers:
            # Check TTL expiration
            if worker.is_expired:
                # Timeout - kill and mark
                kill_tmux_session(worker.session_name)
                output = get_worker_output(worker)
                status, task_id, message, lines = parse_worker_result(output)
                if status == "UNKNOWN":
                    status = "TIMEOUT"
                    message = f"Worker exceeded {worker.ttl_minutes} minute TTL"
                handle_worker_death(state, worker, status, message, lines)
                workers_to_remove.append(worker)
                continue

            # Check if session still running
            active_sessions = get_active_tmux_sessions()
            session_alive = worker.session_name in active_sessions

            if not session_alive:
                # Session ended - parse output for result
                output = get_worker_output(worker)
                status, task_id, message, lines = parse_worker_result(output)
                cleanup_worker_session(worker)
                handle_worker_death(state, worker, status, message, lines)
                workers_to_remove.append(worker)

        # Remove completed workers from active list
        for worker in workers_to_remove:
            if worker in state.spawner_state.active_workers:
                state.spawner_state.active_workers.remove(worker)

        # Sleep for 1 second before next check
        await asyncio.sleep(1)


def monitor_workers_sync(state: SwarmState) -> SwarmState:
    """Synchronous single-pass worker check.

    Called from main loop to check workers without blocking.

    Args:
        state: SwarmState to check

    Returns:
        Updated state
    """
    from .spawner import (
        get_worker_output, parse_worker_result, cleanup_worker_session,
        get_active_tmux_sessions, kill_tmux_session
    )

    workers_to_remove = []

    for worker in state.spawner_state.active_workers:
        # Check TTL expiration
        if worker.is_expired:
            # Timeout - kill and mark
            kill_tmux_session(worker.session_name)
            output = get_worker_output(worker)
            status, task_id, message, lines = parse_worker_result(output)
            if status == "UNKNOWN":
                status = "TIMEOUT"
                message = f"Worker exceeded {worker.ttl_minutes} minute TTL"
            handle_worker_death(state, worker, status, message, lines)
            workers_to_remove.append(worker)
            continue

        # Check if session still running
        active_sessions = get_active_tmux_sessions()
        session_alive = worker.session_name in active_sessions

        if not session_alive:
            # Session ended - parse output for result
            output = get_worker_output(worker)
            status, task_id, message, lines = parse_worker_result(output)
            cleanup_worker_session(worker)
            handle_worker_death(state, worker, status, message, lines)
            workers_to_remove.append(worker)

    # Remove completed workers from active list
    for worker in workers_to_remove:
        if worker in state.spawner_state.active_workers:
            state.spawner_state.active_workers.remove(worker)

    return state


# === MCP Integration ===

def mcp_connect() -> bool:
    """Connect to MCP server (sync wrapper)."""
    client = get_client()
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(client.connect())
    except RuntimeError:
        # No event loop, create one
        try:
            return asyncio.run(client.connect())
        except Exception:
            return False
    except Exception:
        # Connection failed (server not running, etc.)
        return False


def mcp_call(method: str, params: dict = None):
    """Make a sync MCP call."""
    client = get_client()
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(client.send_command(method, params))
    except RuntimeError:
        return asyncio.run(client.send_command(method, params))


# === RAG Brain Integration ===

def refresh_rag_state(state: SwarmState) -> SwarmState:
    """Refresh RAG Brain connection status and data."""
    rag_client = get_rag_client()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def _fetch_rag_data():
        connected = await rag_client.health()
        stats = await rag_client.stats() if connected else None
        concepts = await rag_client.concepts() if connected else []
        return connected, stats, concepts

    try:
        connected, stats, concepts = loop.run_until_complete(_fetch_rag_data())
        state.rag_connected = connected
        state.brain_state.connected = connected
        state.brain_state.stats = stats or {}
        state.brain_state.concepts = concepts or []
        state.brain_state.last_refresh = datetime.now()
        state.brain_state.error = None
    except Exception as e:
        state.rag_connected = False
        state.brain_state.connected = False
        state.brain_state.error = str(e)

    return state


def refresh_state_from_mcp(state: SwarmState) -> SwarmState:
    """Refresh state from MCP server including tasks by lane."""
    client = get_client()
    if not client.connected:
        state.mcp_connected = False
        return state

    # Fetch swarm status
    response = mcp_call("swarm_status")
    if response.success and response.data:
        data = response.data
        state.wave = data.get("wave", 0)
        state.active_zerglings = data.get("active_zerglings", [])
        state.completed_tasks = data.get("completed_tasks", [])
        state.pending_tasks = data.get("pending_tasks", [])
        state.last_updated = data.get("last_updated", "")
        state.mcp_connected = True
        state.mcp_last_ping = datetime.now()
        state.status_manager.set_message("Connected to MCP", level="success")
    else:
        state.mcp_connected = False
        state.status_manager.set_message(f"MCP: {response.error or 'Disconnected'}", level="warning")

    # Fetch tasks by lane from MCP
    mcp_tasks = fetch_tasks_from_mcp()
    if mcp_tasks:
        state.tasks_by_lane = mcp_tasks

    return state


def load_state() -> SwarmState:
    """Load swarm state from STATE.json and scan directories."""
    state = SwarmState()

    # Load STATE.json
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
                state.wave = data.get("wave", 0)
                state.active_zerglings = data.get("active_zerglings", [])
                state.completed_tasks = data.get("completed_tasks", [])
                state.pending_tasks = data.get("pending_tasks", [])
                state.last_updated = data.get("last_updated", "")
        except (json.JSONDecodeError, IOError):
            pass

    # Scan tasks by lane
    state.tasks_by_lane = scan_tasks()

    # Scan inbox
    state.inbox_results = scan_inbox()

    return state


def save_state(state: SwarmState) -> None:
    """Save state back to STATE.json atomically."""
    data = {
        "wave": state.wave,
        "active_zerglings": state.active_zerglings,
        "completed_tasks": state.completed_tasks,
        "pending_tasks": state.pending_tasks,
        "last_updated": datetime.now().isoformat()
    }
    temp = STATE_FILE.with_suffix(".tmp")
    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk
        temp.replace(STATE_FILE)
    except (IOError, OSError):
        # Clean up temp file on failure
        try:
            temp.unlink()
        except OSError:
            pass
        raise


def _preserve_transient_state(old_state: SwarmState, new_state: SwarmState) -> None:
    """Preserve transient state fields when refreshing from file/MCP."""
    # UI state
    new_state.selected_building = old_state.selected_building
    new_state.selected_task = old_state.selected_task
    # status_manager and refresh_controller are preserved below
    # Building panel states
    new_state.museum_state = old_state.museum_state
    new_state.apartments_state = old_state.apartments_state
    new_state.school_state = old_state.school_state
    new_state.mcdonalds_state = old_state.mcdonalds_state
    new_state.newspaper_state = old_state.newspaper_state
    new_state.brain_state = old_state.brain_state
    # Daemon state (CRITICAL)
    new_state.daemon_config = old_state.daemon_config
    new_state.daemons_state = old_state.daemons_state
    new_state.researcher_daemon = old_state.researcher_daemon
    new_state.teacher_daemon = old_state.teacher_daemon
    new_state.researcher_active = old_state.researcher_active
    new_state.teacher_active = old_state.teacher_active
    # Events and history
    new_state.radio_events = old_state.radio_events
    new_state.cemetery = old_state.cemetery
    new_state.completed_workers = old_state.completed_workers
    new_state._event_queue = old_state._event_queue
    # New managers
    new_state.status_manager = old_state.status_manager
    new_state.refresh_controller = old_state.refresh_controller
    # Visibility flags
    new_state.newspaper_visible = old_state.newspaper_visible
    new_state.school_visible = old_state.school_visible
    new_state.museum_visible = old_state.museum_visible
    new_state.brain_visible = old_state.brain_visible
    new_state.mcdonalds_visible = old_state.mcdonalds_visible
    new_state.daemons_visible = old_state.daemons_visible
    new_state.rag_connected = old_state.rag_connected
    # Wave 5/7 states
    new_state.spawn_confirm_pending = old_state.spawn_confirm_pending
    new_state.decompose_mode = old_state.decompose_mode
    new_state.decompose_goal = old_state.decompose_goal
    new_state.draft_tasks = old_state.draft_tasks


def refresh_state(state: SwarmState) -> SwarmState:
    """Refresh state from MCP (if connected) or disk."""
    client = get_client()

    # Try MCP first if connected
    if client.connected:
        state = refresh_state_from_mcp(state)
        # refresh_state_from_mcp already fetches tasks via MCP
        # Only need to scan inbox locally (MCP doesn't provide inbox yet)
        state.inbox_results = scan_inbox()
    else:
        # Fall back to file-based state
        new_state = load_state()
        _preserve_transient_state(state, new_state)
        new_state.mcp_connected = False
        state = new_state

    # Update daemon status indicators
    # Researcher is active if newspaper has watch items
    state.researcher_active = bool(state.newspaper_state.watch_list)
    # Teacher is active if school has lane knowledge
    state.teacher_active = bool(state.school_state.lane_knowledge)

    # Update spawner state - check active workers
    if state.real_spawn_enabled and state.spawner_state.active_workers:
        state.spawner_state = collect_completed(state.spawner_state)

    return state


def scan_tasks(use_mcp: bool = True) -> dict:
    """Scan TASKS directory for all task cards, using MCP when available.

    Args:
        use_mcp: If True, try to fetch from MCP first. Defaults to True.

    Returns:
        Dict mapping lane names to lists of task dicts with id, status, type.
    """
    # Try MCP first if requested
    if use_mcp:
        client = get_client()
        if client.connected:
            mcp_tasks = fetch_tasks_from_mcp()
            if mcp_tasks:
                return mcp_tasks

    # Fall back to file-based scanning
    tasks = {}
    for lane in LANES:
        lane_dir = TASKS_DIR / lane
        tasks[lane] = []
        if lane_dir.exists():
            for task_file in lane_dir.glob("*.md"):
                task_id = task_file.stem
                status = "PENDING"
                task_type = "TASK"
                # Quick parse for status - supports both formats:
                # "Status: PENDING" and "| Status | PENDING |"
                try:
                    content = task_file.read_text(encoding="utf-8", errors="replace")
                    for line in content.split("\n"):
                        # Table format: | Status | VALUE |
                        if "| Status |" in line:
                            parts = line.split("|")
                            if len(parts) >= 3:
                                status = parts[2].strip()
                        # Key-value format: Status: VALUE
                        elif "Status:" in line:
                            status = line.split(":")[-1].strip()
                        # Table format: | Type | VALUE |
                        if "| Type |" in line:
                            parts = line.split("|")
                            if len(parts) >= 3:
                                task_type = parts[2].strip()
                        # Key-value format: Type: VALUE
                        elif "Type:" in line:
                            task_type = line.split(":")[-1].strip()
                except IOError:
                    pass
                tasks[lane].append({
                    "id": task_id,
                    "status": status,
                    "type": task_type
                })
    return tasks


def scan_inbox() -> list:
    """Scan INBOX for results."""
    results = []
    if INBOX_DIR.exists():
        for result_file in INBOX_DIR.glob("*_RESULT.md"):
            task_id = result_file.stem.replace("_RESULT", "")
            results.append(task_id)
    return results


def fetch_tasks_from_mcp() -> dict:
    """Fetch tasks from MCP server by lane.

    Returns:
        Dict mapping lane names to lists of task dicts with id, status, type.
    """
    client = get_client()
    if not client.connected:
        return {}

    tasks_by_lane = {}
    for lane in LANES:
        try:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(client.task_list(lane))
        except RuntimeError:
            response = asyncio.run(client.task_list(lane))

        if response.success and response.data:
            lane_tasks = []
            for task_data in response.data:
                task_id = task_data.get("task_id", "")
                task_path = task_data.get("path", "")

                # Try to parse status and type from file content
                status = "PENDING"
                task_type = "TASK"
                if task_path:
                    try:
                        task_file = Path(task_path)
                        if task_file.exists():
                            content = task_file.read_text(encoding="utf-8", errors="replace")
                            for line in content.split("\n"):
                                if "| Status |" in line:
                                    parts = line.split("|")
                                    if len(parts) >= 3:
                                        status = parts[2].strip()
                                if "| Type |" in line:
                                    parts = line.split("|")
                                    if len(parts) >= 3:
                                        task_type = parts[2].strip()
                    except (IOError, OSError):
                        pass

                lane_tasks.append({
                    "id": task_id,
                    "status": status,
                    "type": task_type
                })
            tasks_by_lane[lane] = lane_tasks
        else:
            tasks_by_lane[lane] = []

    return tasks_by_lane


# === Terminal Input Handling ===
_original_terminal_settings = None

def _restore_terminal():
    """Global terminal restoration for crash/signal safety."""
    global _original_terminal_settings
    if _original_terminal_settings:
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, _original_terminal_settings)
        except Exception:
            pass

class TerminalInput:
    """Handle non-blocking keyboard input with raw mode."""

    def __init__(self):
        self.old_settings = None

    def __enter__(self):
        """Enter raw mode for single-key input."""
        global _original_terminal_settings
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            _original_terminal_settings = self.old_settings
            atexit.register(_restore_terminal)
            # Handle both SIGTERM and SIGINT for proper cleanup
            signal.signal(signal.SIGTERM, lambda s, f: _restore_terminal())
            signal.signal(signal.SIGINT, lambda s, f: _restore_terminal())
            tty.setraw(sys.stdin.fileno())
        except termios.error:
            # Not a TTY (e.g., piped input)
            self.old_settings = None
        return self

    def __exit__(self, *args):
        """Restore terminal settings."""
        if self.old_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def get_key(self, timeout: float = 0.1) -> Optional[str]:
        """Get a single key press without blocking."""
        if self.old_settings is None:
            return None

        if select.select([sys.stdin], [], [], timeout)[0]:
            ch = sys.stdin.read(1)
            # Handle escape sequences for arrow keys
            if ch == '\x1b':
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        if select.select([sys.stdin], [], [], 0.01)[0]:
                            ch3 = sys.stdin.read(1)
                            # Arrow keys
                            if ch3 == 'A': return 'UP'
                            if ch3 == 'B': return 'DOWN'
                            if ch3 == 'C': return 'RIGHT'
                            if ch3 == 'D': return 'LEFT'
                            # Home/End
                            if ch3 == 'H': return 'HOME'
                            if ch3 == 'F': return 'END'
                            # Extended keys (with trailing ~)
                            if ch3 in '123456':
                                if select.select([sys.stdin], [], [], 0.01)[0]:
                                    sys.stdin.read(1)  # Consume trailing ~
                                if ch3 == '1': return 'HOME'
                                if ch3 == '4': return 'END'
                                if ch3 == '5': return 'PGUP'
                                if ch3 == '6': return 'PGDN'
                    elif ch2 == 'O':
                        # Alternative arrow key encoding
                        if select.select([sys.stdin], [], [], 0.01)[0]:
                            ch3 = sys.stdin.read(1)
                            if ch3 == 'A': return 'UP'
                            if ch3 == 'B': return 'DOWN'
                            if ch3 == 'C': return 'RIGHT'
                            if ch3 == 'D': return 'LEFT'
                return 'ESC'
            return ch
        return None


def get_key_nonblocking() -> Optional[str]:
    """Get key without blocking (fallback for non-TTY)."""
    if select.select([sys.stdin], [], [], 0.1)[0]:
        return sys.stdin.read(1)
    return None


# === TUI Rendering ===
def render_header(state: SwarmState) -> Panel:
    """Render the header - Midwestern Zerg town."""
    header_text = Text()
    header_text.append("🌾 ORSON ", style="bold yellow")
    header_text.append("~ The Hive Wears Flannel ~", style="italic magenta")
    header_text.append(f"  │  Wave {state.wave}", style="dim")
    header_text.append(f"  │  🐛 {len(state.spawner_state.active_workers)} working", style="green")

    # Town services status
    header_text.append("  │ ", style="dim")
    # Newspaper (Researcher)
    header_text.append("📰" if state.researcher_active else "·", style="green" if state.researcher_active else "dim")
    # School (Teacher)
    header_text.append("🏫" if state.teacher_active else "·", style="green" if state.teacher_active else "dim")
    # Brain (RAG)
    header_text.append("🧠" if state.rag_connected else "·", style="cyan" if state.rag_connected else "dim")
    # Hive (MCP)
    header_text.append("🐝" if state.mcp_connected else "·", style="magenta" if state.mcp_connected else "dim")

    return Panel(header_text, style="yellow", height=3)


def render_buildings(state: SwarmState) -> Panel:
    """Render the 5 town buildings with Zerg workers."""
    # Town buildings by lane
    BUILDINGS = {
        "KERNEL": ("🏭", "Silo"),
        "ML": ("📚", "Library"),
        "QUANT": ("🏦", "Bank"),
        "DEX": ("⛽", "Gas-n-Sip"),
        "INTEGRATION": ("📮", "PostOffice")
    }

    table = Table(show_header=False, box=None, expand=True)
    for i in range(5):
        table.add_column(ratio=1)

    buildings = []
    for i, lane in enumerate(LANES, 1):
        tasks = state.tasks_by_lane.get(lane, [])
        pending = sum(1 for t in tasks if t["status"] == "PENDING")
        done = sum(1 for t in tasks if t["status"] == "DONE")
        lane_workers = [w for w in state.spawner_state.active_workers if w.lane == lane]

        icon, name = BUILDINGS.get(lane, ("🏠", lane))
        selected = state.selected_building == i

        building = Text()
        building.append(f"{icon} [{i}] ", style="bold" if selected else "dim")
        building.append(f"{name}\n", style="bold reverse" if selected else "")
        building.append(f"📋{pending} ✓{done}", style="dim")

        # Show Zerg workers at this building (max 2, with overflow indicator)
        if lane_workers:
            for worker in lane_workers[:2]:
                remaining = worker.time_remaining
                mins = int(remaining.total_seconds() // 60)
                secs = int(remaining.total_seconds() % 60)
                time_style = "red" if remaining.total_seconds() < 60 else "yellow" if remaining.total_seconds() < 120 else "green"
                building.append(f"\n  🐛 {mins}:{secs:02d}", style=time_style)
            # Show overflow indicator if more workers
            if len(lane_workers) > 2:
                building.append(f"\n  +{len(lane_workers) - 2} more", style="dim italic")

        buildings.append(building)

    table.add_row(*buildings)
    return Panel(table, title="🌾 Town Buildings [1-5]", border_style="yellow")


def render_tasks(state: SwarmState) -> Panel:
    """Render task list for selected building."""
    lane = LANES[state.selected_building - 1]
    BUILDING_NAMES = {"KERNEL": "Silo", "ML": "Library", "QUANT": "Bank", "DEX": "Gas-n-Sip", "INTEGRATION": "PostOffice"}
    tasks = state.tasks_by_lane.get(lane, [])

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Task", width=12)
    table.add_column("Type", width=14)
    table.add_column("Status", width=10)

    STATUS_ICONS = {"PENDING": "⏳", "IN_PROGRESS": "🐛", "DONE": "✓", "PARTIAL": "½", "BLOCKED": "🚫", "FAILED": "✗"}
    STATUS_STYLES = {"PENDING": "yellow", "IN_PROGRESS": "cyan", "DONE": "green", "PARTIAL": "magenta", "BLOCKED": "red", "FAILED": "red bold"}

    for task in tasks[:10]:
        icon = STATUS_ICONS.get(task["status"], "?")
        style = STATUS_STYLES.get(task["status"], "white")
        table.add_row(task["id"], task["type"], Text(f"{icon} {task['status']}", style=style))

    if not tasks:
        table.add_row("(empty)", "-", "-")

    return Panel(table, title=f"📋 {BUILDING_NAMES.get(lane, lane)} Jobs", border_style="cyan")


def render_zerglings(state: SwarmState) -> Panel:
    """Render active Zerg workers in the town."""
    content = Text()

    if state.spawner_state.active_workers:
        for worker in state.spawner_state.active_workers[:5]:
            remaining = worker.time_remaining
            mins = int(remaining.total_seconds() // 60)
            secs = int(remaining.total_seconds() % 60)
            bar_style = "red" if remaining.total_seconds() < 60 else "yellow" if remaining.total_seconds() < 120 else "green"

            content.append(f"🐛 {worker.name[:10]}", style="bold green")
            content.append(f" {worker.task_id}\n", style="dim")

            # Simple progress bar
            progress = worker.progress
            filled = int(10 * progress)
            content.append(f"   [{'█' * filled}{'░' * (10 - filled)}] {mins}:{secs:02d}\n", style=bar_style)

    elif state.active_zerglings:
        for z in state.active_zerglings[:5]:
            content.append(f"🐛 {z.get('name', '?')}", style="green")
            content.append(f" w{z.get('wave', '?')}\n", style="dim")
    else:
        content.append("Larvae dormant...", style="dim italic")

    if state.spawner_state.completed_workers:
        done = len([w for w in state.spawner_state.completed_workers if w.status == "done"])
        if done:
            content.append(f"\n✓ {done} returned", style="dim green")

    return Panel(content, title=f"🐛 Zerglings ({len(state.spawner_state.active_workers)})", border_style="green", height=12)


def render_inbox(state: SwarmState) -> Panel:
    """Render harvest - completed task results."""
    if not state.inbox_results:
        content = Text("Awaiting harvest...", style="dim italic")
    else:
        content = Text()
        for task_id in state.inbox_results[:5]:
            content.append(f"🌽 {task_id}\n", style="yellow")
        if len(state.inbox_results) > 5:
            content.append(f"   +{len(state.inbox_results) - 5} more", style="dim")

    return Panel(content, title=f"🌽 Harvest ({len(state.inbox_results)})", border_style="yellow", height=8)


def render_help() -> Panel:
    """Render help bar."""
    help_text = Text()
    help_text.append("[1-5]", style="cyan")
    help_text.append(" building ", style="dim")
    help_text.append("[d]", style="green")
    help_text.append("ecomp ", style="dim")
    help_text.append("[s]", style="green")
    help_text.append("pawn ", style="dim")
    help_text.append("[c]", style="green")
    help_text.append("ollect ", style="dim")
    help_text.append("[k]", style="red")
    help_text.append("ill ", style="dim")
    help_text.append("[m]", style="magenta")
    help_text.append("useum ", style="dim")
    help_text.append("[b]", style="magenta")
    help_text.append("rain ", style="dim")
    help_text.append("[g]", style="magenta")
    help_text.append("svcs ", style="dim")
    help_text.append("[r]", style="yellow")
    help_text.append("efresh ", style="dim")
    help_text.append("[q]", style="yellow")
    help_text.append("uit", style="dim")

    return Panel(help_text, border_style="dim", height=3)


def render_status(state: SwarmState) -> Panel:
    """Render the Queen's status message."""
    msg = state.status_manager.get_current()
    if msg:
        text = Text(msg.text, style=state.status_manager.get_style())
    else:
        text = Text("The Hive awaits...", style="dim italic")
    return Panel(text, title="👑 Queen", border_style="magenta", height=3)


def render_radio_panel(state: SwarmState, max_events: int = 5) -> Panel:
    """Render the Overlord psionic broadcast."""
    content = Text()
    content.append("KZRG 98.6\n", style="bold yellow")

    events = state.radio_events[-max_events:] if state.radio_events else []

    if events:
        for event in reversed(events):
            timestamp = event.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    timestamp = datetime.now()
            time_str = timestamp.strftime("%H:%M")
            msg = event.get("message", "")[:35]
            content.append(f" {time_str} {msg}\n", style="dim")
    else:
        content.append(" (static...)\n", style="dim italic")

    return Panel(content, border_style="yellow", height=7, title="📻 Overlord Radio")


def render_layout(state: SwarmState) -> Layout:
    """Render the full TUI layout."""
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="buildings", size=5),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=9)
    )

    # Split footer into radio on left, status/help on right
    layout["footer"].split_row(
        Layout(name="radio", ratio=1),
        Layout(name="status_area", ratio=2)
    )
    layout["status_area"].split_column(
        Layout(name="status", size=3),
        Layout(name="help", size=3)
    )

    layout["header"].update(render_header(state))
    layout["buildings"].update(render_buildings(state))

    # Main area split into tasks and sidebar (or overlay panels)
    if state.daemons_visible:
        # Show daemons control panel as modal overlay
        layout["main"].update(render_daemons_panel(
            state.daemons_state,
            researcher_daemon=state.researcher_daemon,
            teacher_daemon=state.teacher_daemon,
            rag_connected=state.rag_connected,
            rag_stats=state.brain_state.stats if state.brain_state else {},
            mcp_connected=state.mcp_connected,
            wave=state.wave
        ))
    elif state.brain_visible:
        # Show brain panel as modal overlay in main area
        layout["main"].update(render_brain_panel(state.brain_state))
    elif state.museum_visible:
        # Show museum as modal overlay in main area
        layout["main"].update(render_museum(state.museum_state, width=70))
    else:
        # Main area: tasks on left, sidebar on right
        layout["main"].split_row(
            Layout(name="tasks", ratio=3),
            Layout(name="sidebar", size=30)
        )
        layout["main"]["tasks"].update(render_tasks(state))

        # Sidebar: fixed heights for both panels
        layout["main"]["sidebar"].split_column(
            Layout(name="zerglings", size=12),
            Layout(name="inbox", size=8)
        )
        layout["main"]["sidebar"]["zerglings"].update(render_zerglings(state))
        layout["main"]["sidebar"]["inbox"].update(render_inbox(state))

    layout["radio"].update(render_radio_panel(state))
    layout["help"].update(render_help())
    layout["status"].update(render_status(state))

    return layout


# === Task Decomposition (Wave 7) ===
def decompose_goal_into_tasks(goal: str, wave: int) -> list:
    """Decompose a goal into 5 microtasks (template-based for MVP).

    Creates a balanced wave:
    - 2 implementation tasks (ADD_STUB, ADD_PURE_FN)
    - 2 validation tasks (ADD_TEST, ADD_ASSERTS)
    - 1 quality task (DOC_SNIPPET)
    """
    # Determine lane from goal keywords
    lane = "KERNEL"  # default
    goal_lower = goal.lower()

    if any(kw in goal_lower for kw in ["model", "train", "ml", "inference", "neural", "embedding"]):
        lane = "ML"
    elif any(kw in goal_lower for kw in ["quant", "backtest", "strategy", "trading", "alpha"]):
        lane = "QUANT"
    elif any(kw in goal_lower for kw in ["dex", "solana", "swap", "jupiter", "jito", "transaction"]):
        lane = "DEX"
    elif any(kw in goal_lower for kw in ["config", "cli", "integration", "api", "wire", "glue"]):
        lane = "INTEGRATION"

    # Get prefix for task IDs
    prefix_map = {
        "KERNEL": "K",
        "ML": "M",
        "QUANT": "Q",
        "DEX": "D",
        "INTEGRATION": "INT-"
    }
    prefix = prefix_map[lane]
    base_num = wave * 100

    # Truncate goal for display if too long
    goal_short = goal[:50] + "..." if len(goal) > 50 else goal

    # Format task ID appropriately (INT- uses different format)
    def fmt_id(num):
        if prefix == "INT-":
            return f"INT-{num:03d}"
        return f"{prefix}{num:03d}"

    return [
        {
            "id": fmt_id(base_num + 1),
            "lane": lane,
            "type": "ADD_STUB",
            "objective": f"Create stub for: {goal_short}"
        },
        {
            "id": fmt_id(base_num + 2),
            "lane": lane,
            "type": "ADD_PURE_FN",
            "objective": f"Implement core logic: {goal_short}"
        },
        {
            "id": fmt_id(base_num + 3),
            "lane": lane,
            "type": "ADD_TEST",
            "objective": f"Add tests for: {goal_short}"
        },
        {
            "id": fmt_id(base_num + 4),
            "lane": lane,
            "type": "ADD_ASSERTS",
            "objective": f"Add validation for: {goal_short}"
        },
        {
            "id": fmt_id(base_num + 5),
            "lane": lane,
            "type": "DOC_SNIPPET",
            "objective": f"Document: {goal_short}"
        },
    ]


def inject_rag_knowledge(task: dict, state: SwarmState) -> tuple[dict, str]:
    """Inject RAG knowledge into a task's objective.

    Args:
        task: Task dict with id, lane, type, objective
        state: SwarmState with school_state containing lane_knowledge

    Returns:
        Tuple of (updated task dict, log message)
    """
    lane = task.get("lane", "KERNEL")
    objective = task.get("objective", "")

    # Get knowledge for this lane from school state
    lane_knowledge = state.school_state.lane_knowledge.get(lane, [])

    if not lane_knowledge:
        # Try to fetch fresh knowledge
        lane_knowledge = fetch_lane_knowledge_sync(lane)

    if lane_knowledge:
        # Get the most relevant memory (first one)
        memory = lane_knowledge[0]
        if isinstance(memory, dict):
            knowledge_content = memory.get("content", memory.get("text", ""))
        else:
            knowledge_content = str(memory)

        # Truncate if too long
        if len(knowledge_content) > 200:
            knowledge_content = knowledge_content[:197] + "..."

        # Inject into objective
        if knowledge_content:
            task["objective"] = f"{objective}\n\n[RAG Knowledge]: {knowledge_content}"
            task["injected_knowledge"] = knowledge_content

            # Generate worker name for log
            from .state import generate_short_name
            worker_name = generate_short_name()
            log_msg = f"{worker_name} learned: {knowledge_content[:50]}..."
            return task, log_msg

    return task, ""


# === Commands ===
def cmd_decompose(state: SwarmState, console: Console) -> SwarmState:
    """Decompose a goal into 5 microtasks.

    Two-phase operation:
    1. First call: Enter decompose mode, show prompt
    2. Second call (with goal): Create tasks via MCP
    """
    if not state.decompose_mode:
        # Phase 1: Enter decompose mode
        state.decompose_mode = True
        state.decompose_goal = ""
        state.draft_tasks = []
        state.status_manager.set_message("Enter goal (then press Enter): _", level="info")
        return state

    # Phase 2: We have a goal, decompose it
    if state.decompose_goal:
        goal = state.decompose_goal.strip()

        if not goal:
            state.decompose_mode = False
            state.decompose_goal = ""
            state.status_manager.set_message("Decompose cancelled (empty goal)", level="info")
            return state

        # Generate 5 microtasks based on goal
        tasks = decompose_goal_into_tasks(goal, state.wave + 1)

        # Inject RAG knowledge into each task
        knowledge_logs = []
        for i, task in enumerate(tasks):
            task, log_msg = inject_rag_knowledge(task, state)
            if log_msg:
                knowledge_logs.append(log_msg)
            tasks[i] = task

        # Create tasks via MCP
        created = 0
        for task in tasks:
            response = mcp_call("task_create", {
                "task_id": task["id"],
                "lane": task["lane"],
                "task_type": task["type"],
                "objective": task["objective"]
            })
            if response.success:
                created += 1

        # Store draft tasks for display
        state.draft_tasks = tasks

        # Reset decompose mode
        state.decompose_mode = False
        state.decompose_goal = ""

        # Update status with result
        goal_preview = goal[:30] + "..." if len(goal) > 30 else goal
        if created > 0:
            if knowledge_logs:
                # Show one knowledge injection log
                state.status_manager.set_message(f"Created {created}/5 tasks. {knowledge_logs[0]}", level="success")
            else:
                state.status_manager.set_message(f"Created {created}/5 tasks from: {goal_preview}", level="success")
        else:
            state.status_manager.set_message(f"Drafted {len(tasks)} tasks (MCP offline): {goal_preview}", level="warning")

        # Refresh task list to show new tasks
        state.tasks_by_lane = scan_tasks()

    return state


def cmd_spawn_wave(state: SwarmState) -> SwarmState:
    """Spawn a new wave of zerglings via MCP with real tmux spawning."""
    # Confirmation pattern - first press shows warning
    if not state.spawn_confirm_pending:
        state.spawn_confirm_pending = True
        # Show what will be spawned
        pending_count = sum(
            len([t for t in tasks if t.get("status") == "PENDING"])
            for tasks in state.tasks_by_lane.values()
        )
        if state.real_spawn_enabled and state.tmux_available and state.claude_available:
            state.status_manager.set_message(f"Press 's' to spawn {pending_count} real workers (tmux)", level="info")
        else:
            state.status_manager.set_message(f"Press 's' to confirm wave spawn ({pending_count} tasks)", level="info")
        return state

    # Reset confirmation state
    state.spawn_confirm_pending = False

    # Gather pending tasks from all lanes
    tasks_to_spawn = []
    for lane, tasks in state.tasks_by_lane.items():
        for task in tasks:
            if task.get("status") == "PENDING":
                # Read full task content if available
                task_file = TASKS_DIR / lane / f"{task['id']}.md"
                objective = ""
                if task_file.exists():
                    try:
                        content = task_file.read_text(encoding="utf-8", errors="replace")
                        # Extract objective from task file
                        for line in content.split("\n"):
                            if line.startswith("##") and "Objective" in line:
                                # Next non-empty line is objective
                                idx = content.find(line) + len(line)
                                remaining = content[idx:].strip()
                                objective = remaining.split("\n")[0].strip()
                                break
                    except IOError:
                        pass

                tasks_to_spawn.append({
                    "id": task["id"],
                    "lane": lane,
                    "type": task.get("type", "TASK"),
                    "objective": objective or f"Complete task {task['id']}"
                })

    if not tasks_to_spawn:
        state.status_manager.set_message("No pending tasks to spawn", level="info")
        return state

    # Limit to 5 tasks per wave
    tasks_to_spawn = tasks_to_spawn[:5]

    # Inject RAG knowledge into tasks
    knowledge_logs = []
    for i, task in enumerate(tasks_to_spawn):
        task, log_msg = inject_rag_knowledge(task, state)
        if log_msg:
            knowledge_logs.append(log_msg)
        tasks_to_spawn[i] = task

    # Real spawning with tmux
    if state.real_spawn_enabled and state.tmux_available and state.claude_available:
        # Increment wave
        state.wave += 1

        # Ensure worker pool has workers
        if len(state.apartments_state.idle_workers) < len(tasks_to_spawn):
            state = init_worker_pool(state, len(tasks_to_spawn) - len(state.apartments_state.idle_workers))

        # Add radio announcement
        add_radio_event(state, f"\U0001f4e3 Wave {state.wave} assembling... {len(tasks_to_spawn)} workers heading to work!", "\U0001f4e3")

        # Spawn workers from pool
        from .spawner import spawn_worker
        spawned_count = 0
        for task in tasks_to_spawn:
            # Get worker from pool
            idle_worker = spawn_worker_from_pool(state.apartments_state)
            worker_name = idle_worker.name if idle_worker else None

            # Spawn with tmux
            spawned = spawn_worker(task, SWARM_ROOT, state.wave, worker_name)
            if spawned:
                state.spawner_state.active_workers.append(spawned)
                spawned_count += 1
                state.apartments_state.total_spawned += 1

                # Add radio event for this worker
                lane_icon = {
                    "KERNEL": "\U0001f3ed",  # Factory
                    "ML": "\U0001f4da",      # Books
                    "QUANT": "\U0001f3e6",   # Bank
                    "DEX": "\u26fd",         # Gas pump
                    "INTEGRATION": "\U0001f4ee"  # Mailbox
                }.get(task["lane"], "\U0001f477")  # Construction worker

                add_radio_event(
                    state,
                    f"\U0001f477 {spawned.name} heading to {task['lane']} [{task['id']}]",
                    lane_icon
                )

        state.spawner_state.wave = state.wave
        state.spawner_state.last_spawn = datetime.now()

        worker_names = [w.name for w in state.spawner_state.active_workers[-spawned_count:]]
        names_str = ", ".join(worker_names[:3])
        if len(worker_names) > 3:
            names_str += f" +{len(worker_names) - 3}"

        state.status_manager.set_message(f"Wave {state.wave}: {spawned_count} workers spawned! ({names_str})", level="success")

        # Also notify MCP if connected
        client = get_client()
        if client.connected:
            mcp_call("wave_increment")

        save_state(state)
    else:
        # Fallback to MCP-only spawning
        client = get_client()
        if not client.connected:
            state.status_manager.set_message("Cannot spawn: MCP not connected, tmux not available", level="error")
            return state

        response = mcp_call("wave_increment")
        if response.success:
            data = response.data
            state.wave = data.get("new_wave", state.wave + 1)
            voiceline = data.get("voiceline", "")
            state.status_manager.set_message(f"Wave {state.wave} spawned! {voiceline}", level="success")
            save_state(state)
        else:
            state.status_manager.set_message(f"Spawn failed: {response.error}", level="error")

    return state


def cmd_collect_results_from_files(state: SwarmState) -> SwarmState:
    """Collect results from inbox using file-based method (fallback)."""
    new_completed = 0
    completed_set = set(state.completed_tasks)

    for task_id in state.inbox_results:
        if task_id not in completed_set:
            completed_set.add(task_id)
            new_completed += 1

    state.completed_tasks = list(completed_set)
    save_state(state)
    state.status_manager.set_message(f"Collected {new_completed} results. Total: {len(completed_set)}", level="success")
    return state


def cmd_collect_results(state: SwarmState) -> SwarmState:
    """Collect results from inbox via MCP or fallback to files."""
    client = get_client()
    if not client.connected:
        # Fall back to file-based collection
        return cmd_collect_results_from_files(state)

    # First check what's in inbox via MCP
    inbox_response = mcp_call("inbox_list")
    task_ids = []
    if inbox_response.success:
        inbox_items = inbox_response.data or []
        if not inbox_items:
            state.status_manager.set_message("Inbox is empty", level="info")
            return state

        # Extract task IDs from inbox items
        task_ids = [item.get("task_id", "") for item in inbox_items if item.get("task_id")]
        if task_ids:
            # Show what we're collecting (up to 3 task IDs)
            preview = ", ".join(task_ids[:3])
            if len(task_ids) > 3:
                preview += f"...+{len(task_ids) - 3} more"
            state.status_manager.set_message(f"Collecting: {preview}...", level="info")
    else:
        # inbox_list failed, try wave_collect anyway
        state.status_manager.set_message("Checking inbox via wave_collect...", level="info")

    # Collect via MCP wave_collect
    response = mcp_call("wave_collect")
    if response.success:
        data = response.data or {}
        collected = data.get("collected", 0)
        total = data.get("total_completed", 0)
        voiceline = data.get("voiceline", "")

        # Update local state with collected task IDs
        if task_ids:
            state.completed_tasks = list(set(state.completed_tasks) | set(task_ids))
        state.inbox_results = []  # Clear inbox after collection

        # === RAG Feedback Loop (Wave 17) ===
        rag_client = get_rag_client()
        feedback_sent = 0
        wave_stored = False

        if collected > 0:
            # Send feedback for completed workers
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()

            # Process cemetery feedback (workers with memory_ids)
            # Note: In full implementation, workers would have memory_id from pre-spawn
            # For now, we store the wave outcome
            feedback_sent = 0  # Would be: loop.run_until_complete(process_cemetery_feedback(...))

            # Store wave outcome as memory
            wave_outcome = loop.run_until_complete(
                store_wave_outcome(state.wave, [], rag_client)
            )
            if wave_outcome:
                wave_stored = True

        # Build status message
        status_parts = [f"Collected {collected} results (total: {total})"]
        if wave_stored:
            status_parts.append("Wave outcome stored")
        if feedback_sent > 0:
            status_parts.append(f"{feedback_sent} feedback sent")
        if voiceline:
            status_parts.append(voiceline)
        state.status_manager.set_message(". ".join(status_parts), level="success")

        # Save state to disk
        save_state(state)
    else:
        error_msg = response.error or "Unknown error"
        state.status_manager.set_message(f"Collection failed: {error_msg}", level="error")
        # Fall back to file-based if MCP fails
        return cmd_collect_results_from_files(state)

    return state


def cmd_view_task(state: SwarmState, console: Console) -> SwarmState:
    """View task detail (would show in popup/modal)."""
    lane = LANES[state.selected_building - 1]
    tasks = state.tasks_by_lane.get(lane, [])
    if tasks:
        state.status_manager.set_message(f"View task: {tasks[0]['id']} (full view in web UI)", level="info")
    else:
        state.status_manager.set_message("No tasks to view in this lane", level="info")
    return state


def cmd_select_building(state: SwarmState, num: int) -> SwarmState:
    """Select a building/lane."""
    if 1 <= num <= 5:
        state.selected_building = num
        state.status_manager.set_message(f"Selected: {LANES[num - 1]}", level="info")
    return state


# === Key Handler ===
def handle_key(state: SwarmState, key: str, console: Console) -> tuple[SwarmState, bool]:
    """Handle a key press. Returns (new_state, should_quit)."""
    # Wave 7: Handle decompose mode input
    if state.decompose_mode:
        if key == '\r' or key == '\n':  # Enter - submit goal
            return cmd_decompose(state, console), False
        elif key == '\x1b':  # Escape - cancel decompose
            state.decompose_mode = False
            state.decompose_goal = ""
            state.status_manager.set_message("Decompose cancelled", level="info")
            return state, False
        elif key == '\x7f' or key == '\x08':  # Backspace (DEL or BS)
            state.decompose_goal = state.decompose_goal[:-1]
            state.status_manager.set_message(f"Enter goal (then press Enter): {state.decompose_goal}_", level="info")
            return state, False
        elif key == '\x03':  # Ctrl+C - quit even in decompose mode
            return state, True
        elif key and len(key) == 1 and key.isprintable():
            if len(state.decompose_goal) < MAX_DECOMPOSE_GOAL_LENGTH:
                state.decompose_goal += key
                state.status_manager.set_message(f"Goal ({len(state.decompose_goal)}/{MAX_DECOMPOSE_GOAL_LENGTH}): {state.decompose_goal[-50:]}_", level="info")
            else:
                state.status_manager.set_message(f"Goal too long (max {MAX_DECOMPOSE_GOAL_LENGTH}). Press Enter.", level="warning")
            return state, False
        # Ignore other keys in decompose mode
        return state, False

    # Cancel spawn confirmation if any key other than 's' is pressed
    if key != 's' and state.spawn_confirm_pending:
        state.spawn_confirm_pending = False
        state.status_manager.set_message("Spawn cancelled", level="info")

    if key == 'q' or key == '\x03':  # q or Ctrl+C
        return state, True
    elif key == 'd':
        state = cmd_decompose(state, console)
    elif key == 's':
        state = cmd_spawn_wave(state)
    elif key == 'c':
        state = cmd_collect_results(state)
    elif key == 'v':
        state = cmd_view_task(state, console)
    elif key == 'k':
        # Kill all active workers (emergency stop)
        if state.spawner_state.active_workers:
            count = len(state.spawner_state.active_workers)
            state.spawner_state = kill_all_workers(state.spawner_state)
            state.status_manager.set_message(f"Killed {count} workers (emergency stop)", level="warning")
        else:
            state.status_manager.set_message("No active workers to kill", level="info")
    elif key == 'r':
        state = refresh_state(state)
        state.status_manager.set_message("State refreshed from disk", level="success")
    elif key == 'h':
        state.status_manager.set_message("d=Decompose s=Spawn c=Collect v=View k=Kill m=Museum n=News b=Brain t=School g=Services R/T=Daemons L=Learn r=Refresh q=Quit", level="info")
    elif key == 'm':
        state.museum_visible = not state.museum_visible
        if state.museum_visible:
            state.museum_state = load_museum_data(SWARM_ROOT)
            state.museum_state.is_visible = True
            # Initialize concept selection if concepts are available
            if state.museum_state.concepts:
                state.museum_state.selected_concept_idx = 0
        state.status_manager.set_message("Museum " + ("opened" if state.museum_visible else "closed"), level="info")
    elif key == 't':
        state.school_visible = not state.school_visible
        if state.school_visible:
            state.school_state.prompts_content = load_prompts(SWARM_ROOT)
            state.school_state.is_visible = True
            # Refresh RAG knowledge for all lanes
            state.school_state = refresh_school_knowledge(state.school_state)
            # Update daemon indicator
            state.teacher_active = bool(state.school_state.lane_knowledge)
        state.status_manager.set_message("School " + ("opened" if state.school_visible else "closed"), level="info")
    elif key == 'f':
        state.mcdonalds_visible = not state.mcdonalds_visible
        if state.mcdonalds_visible:
            state.mcdonalds_state.is_visible = True
        state.status_manager.set_message("McDonald's " + ("opened" if state.mcdonalds_visible else "closed"), level="info")
    elif key == 'n':
        state.newspaper_visible = not state.newspaper_visible
        if state.newspaper_visible:
            # Initialize watch list if empty
            if not state.newspaper_state.watch_list:
                state.newspaper_state.watch_list = init_default_watches(PROJECT_ROOT)
            state.newspaper_state.is_visible = True
            # Update daemon indicator
            state.researcher_active = bool(state.newspaper_state.watch_list)
        else:
            state.newspaper_state.input_mode = False
        state.status_manager.set_message("Newspaper " + ("opened" if state.newspaper_visible else "closed"), level="info")
    # Newspaper input mode handling
    elif state.newspaper_visible and state.newspaper_state.input_mode:
        if key == '\x1b':  # Escape
            state.newspaper_state.input_mode = False
            state.newspaper_state.current_input = ""
            state.status_manager.set_message("Input cancelled", level="info")
        elif key == '\r' or key == '\n':  # Enter - submit
            content = state.newspaper_state.current_input.strip()
            if content:
                # Store to RAG (async call wrapped)
                rag_client = get_rag_client()
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                finding = loop.run_until_complete(
                    store_to_rag(state.newspaper_state, content, "insight", [], rag_client)
                )
                if finding:
                    state.status_manager.set_message(f"{finding.quality_icon} Stored: {finding.quality_label} ({finding.quality:.2f})", level="success")
                else:
                    state.status_manager.set_message("Failed to store to RAG", level="error")
            state.newspaper_state.input_mode = False
            state.newspaper_state.current_input = ""
        elif key == '\x7f':  # Backspace
            state.newspaper_state.current_input = state.newspaper_state.current_input[:-1]
        elif len(key) == 1 and key.isprintable():
            state.newspaper_state.current_input += key
    elif state.newspaper_visible and key == 'a':
        # Enter add research input mode
        state.newspaper_state.input_mode = True
        state.newspaper_state.current_input = ""
        state.status_manager.set_message("Type research content, Enter to submit", level="info")
    elif state.newspaper_visible and key == 'p':
        # Process queue
        rag_client = get_rag_client()
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        processed = loop.run_until_complete(
            process_queue(state.newspaper_state, rag_client, chunk_file)
        )
        state.status_manager.set_message(f"Processed {processed} items from queue", level="success")
    # Museum navigation handling
    elif state.museum_visible and state.museum_state.show_concept_detail:
        # In concept detail view
        if key == '\x1b':  # Escape - back to museum
            state.museum_state.show_concept_detail = False
            state.status_manager.set_message("Back to museum", level="info")
    elif state.museum_visible:
        # Museum main view - handle navigation
        if key == '\x1b':  # Escape - close museum
            state.museum_visible = False
            state.museum_state.is_visible = False
            state.status_manager.set_message("Museum closed", level="info")
        elif key == 'UP':
            # Move selection up
            if state.museum_state.concepts:
                state.museum_state.selected_concept_idx = max(0, state.museum_state.selected_concept_idx - 1)
                concept = state.museum_state.concepts[state.museum_state.selected_concept_idx]
                state.status_manager.set_message(f"Selected: {concept.name}", level="info")
        elif key == 'DOWN':
            # Move selection down
            if state.museum_state.concepts:
                max_idx = len(state.museum_state.concepts) - 1
                state.museum_state.selected_concept_idx = min(max_idx, state.museum_state.selected_concept_idx + 1)
                concept = state.museum_state.concepts[state.museum_state.selected_concept_idx]
                state.status_manager.set_message(f"Selected: {concept.name}", level="info")
        elif key == '\r' or key == '\n':  # Enter - view concept detail
            if state.museum_state.selected_concept_idx >= 0 and state.museum_state.concepts:
                # Load memories for selected concept
                state.museum_state = load_concept_memories(state.museum_state)
                state.museum_state.show_concept_detail = True
                concept = state.museum_state.concepts[state.museum_state.selected_concept_idx]
                state.status_manager.set_message(f"Viewing: {concept.name}", level="info")
        elif key == 'R' or key == 'r':
            # Refresh concepts from RAG
            state.museum_state = refresh_museum_concepts(state.museum_state)
            state.status_manager.set_message("Museum concepts refreshed", level="success")
    elif key == 'b':
        state.brain_visible = not state.brain_visible
        if state.brain_visible:
            state = refresh_rag_state(state)
            state.brain_state.visible = True
        state.status_manager.set_message("Brain " + ("opened" if state.brain_visible else "closed"), level="info")
    elif key == 'R':
        # Toggle researcher daemon
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if state.researcher_daemon and state.researcher_daemon.running:
            # Stop the daemon
            loop.run_until_complete(state.researcher_daemon.stop())
            state.researcher_active = False
            state.status_manager.set_message("Researcher daemon stopped", level="info")
        else:
            # Create and start the daemon
            if not state.researcher_daemon:
                rag_client = get_rag_client()

                def message_callback(msg: str):
                    add_radio_event_async(state, msg, "\U0001f50d")

                state.researcher_daemon = ResearcherDaemon(rag_client, message_callback)
                # Add default watch paths
                state.researcher_daemon.add_watch(PROJECT_ROOT / "src", ["*.py"])
                state.researcher_daemon.add_watch(SWARM_ROOT, ["*.md", "*.json"])

            loop.run_until_complete(state.researcher_daemon.start())
            state.researcher_active = True
            state.status_manager.set_message("Researcher daemon started", level="success")
    elif key == 'T':
        # Toggle teacher daemon
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if state.teacher_daemon and state.teacher_daemon.running:
            # Stop the daemon
            loop.run_until_complete(state.teacher_daemon.stop())
            state.teacher_active = False
            state.status_manager.set_message("Teacher daemon stopped", level="info")
        else:
            # Create and start the daemon
            if not state.teacher_daemon:
                rag_client = get_rag_client()

                def teacher_message_callback(msg: str):
                    add_radio_event_async(state, msg, "\U0001f469\u200d\U0001f3eb")

                state.teacher_daemon = TeacherDaemon(
                    rag_client,
                    prompts_dir=SWARM_ROOT / "PROMPTS",
                    message_callback=teacher_message_callback
                )

            loop.run_until_complete(state.teacher_daemon.start())
            state.teacher_active = True
            state.status_manager.set_message("Teacher daemon started", level="success")
    elif key == 'L':
        # Force teach all lanes now
        if state.teacher_daemon:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(state.teacher_daemon.teach_now())
            state.status_manager.set_message("Force-taught all lanes", level="success")
        else:
            state.status_manager.set_message("Teacher daemon not initialized (press T first)", level="warning")
    elif key == 'g':
        # Toggle daemon control panel
        state.daemons_visible = not state.daemons_visible
        state.daemons_state.is_visible = state.daemons_visible
        state.status_manager.set_message("Services panel " + ("opened" if state.daemons_visible else "closed"), level="info")
    elif key in '12345':
        state = cmd_select_building(state, int(key))
    elif key == 'LEFT':
        state.selected_building = max(1, state.selected_building - 1)
        state.status_manager.set_message(f"Selected: {LANES[state.selected_building - 1]}", level="info")
    elif key == 'RIGHT':
        state.selected_building = min(5, state.selected_building + 1)
        state.status_manager.set_message(f"Selected: {LANES[state.selected_building - 1]}", level="info")

    return state, False


# === Main Entry Point ===
def main():
    """Main CLI entry point with Rich Live display."""
    console = Console()

    # Print banner
    banner = """
    [magenta bold]
     ██████╗ ██████╗ ███████╗ ██████╗ ███╗   ██╗
    ██╔═══██╗██╔══██╗██╔════╝██╔═══██╗████╗  ██║
    ██║   ██║██████╔╝███████╗██║   ██║██╔██╗ ██║
    ██║   ██║██╔══██╗╚════██║██║   ██║██║╚██╗██║
    ╚██████╔╝██║  ██║███████║╚██████╔╝██║ ╚████║
     ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
    [/magenta bold]
    [cyan italic]"The hive wears flannel"[/cyan italic]
    """
    console.print(banner)
    console.print("[dim]Loading swarm state...[/dim]")

    # Initialize state from files first
    state = load_state()

    # Set initial welcome message
    state.status_manager.set_message("Welcome to Orson. Press 'h' for help.", level="info", ttl=10.0)

    # Try to connect to MCP server
    console.print("[dim]Connecting to MCP server...[/dim]")
    if mcp_connect():
        console.print("[green]🟢 MCP connected![/green]")
        state = refresh_state_from_mcp(state)
    else:
        console.print("[yellow]🔴 MCP not available, using file state[/yellow]")
        state.mcp_connected = False

    # Check spawner availability (tmux + claude)
    console.print("[dim]Checking spawner availability...[/dim]")
    state.tmux_available = check_tmux_available()
    state.claude_available = check_claude_available()

    if state.tmux_available and state.claude_available:
        console.print("[green]🟢 Real spawning enabled (tmux + claude)[/green]")
        state.spawner_state = get_spawner_state()
    else:
        missing = []
        if not state.tmux_available:
            missing.append("tmux")
        if not state.claude_available:
            missing.append("claude")
        console.print(f"[yellow]🔴 Real spawning disabled (missing: {', '.join(missing)})[/yellow]")
        state.real_spawn_enabled = False

    # Check if SWARM directory exists
    if not SWARM_ROOT.exists():
        console.print(f"[red]SWARM directory not found at {SWARM_ROOT}[/red]")
        console.print("[yellow]Creating directory structure...[/yellow]")
        SWARM_ROOT.mkdir(parents=True, exist_ok=True)
        TASKS_DIR.mkdir(exist_ok=True)
        INBOX_DIR.mkdir(exist_ok=True)
        OUTBOX_DIR.mkdir(exist_ok=True)
        for lane in LANES:
            (TASKS_DIR / lane).mkdir(exist_ok=True)

    # Auto-start daemons if configured
    if state.daemon_config.researcher_autostart or state.daemon_config.teacher_autostart:
        console.print("[dim]Auto-starting daemons...[/dim]")
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        rag_client = get_rag_client()

        # Auto-start researcher daemon
        if state.daemon_config.researcher_autostart:
            def researcher_msg_callback(msg: str):
                add_radio_event_async(state, msg, "\U0001f50d")

            state.researcher_daemon = ResearcherDaemon(rag_client, researcher_msg_callback)
            for path_str in state.daemon_config.researcher_watch_paths:
                path = Path(path_str)
                if not path.is_absolute():
                    path = PROJECT_ROOT / path_str
                state.researcher_daemon.add_watch(path, state.daemon_config.researcher_patterns)
            state.researcher_daemon.poll_interval = state.daemon_config.researcher_poll_interval
            loop.run_until_complete(state.researcher_daemon.start())
            state.researcher_active = True
            console.print("[green]  🔍 Researcher daemon started[/green]")

        # Auto-start teacher daemon
        if state.daemon_config.teacher_autostart:
            def teacher_msg_callback(msg: str):
                add_radio_event_async(state, msg, "\U0001f469\u200d\U0001f3eb")

            state.teacher_daemon = TeacherDaemon(
                rag_client,
                prompts_dir=SWARM_ROOT / "PROMPTS",
                message_callback=teacher_msg_callback
            )
            state.teacher_daemon.lesson_interval = state.daemon_config.teacher_interval
            loop.run_until_complete(state.teacher_daemon.start())
            state.teacher_active = True
            console.print("[green]  👩‍🏫 Teacher daemon started[/green]")

    console.print("[green]Starting Orson CLI...[/green]")
    console.print("[dim]Press 'h' for help, 'q' to quit[/dim]\n")

    try:
        with TerminalInput() as term_input:
            # Low refresh rate for stability - RefreshController handles smart updates
            # screen=True uses alternate screen buffer (like vim/less) for clean display
            with Live(render_layout(state), refresh_per_second=1, console=console, screen=True) as live:
                last_state_refresh = datetime.now()
                state_refresh_interval = 2.0  # Refresh from disk every 2 seconds

                while True:
                    # Flush any pending radio events from async callbacks
                    flush_event_queue(state)

                    # Refresh state from disk periodically (not on every loop)
                    now = datetime.now()
                    if (now - last_state_refresh).total_seconds() >= state_refresh_interval:
                        state = refresh_state(state)
                        last_state_refresh = now

                    # Monitor workers (only if we have active workers)
                    if state.spawner_state.active_workers:
                        state = monitor_workers_sync(state)

                    # Use RefreshController to determine if UI needs update
                    if state.refresh_controller.should_render(state):
                        live.update(render_layout(state))
                        state.refresh_controller.mark_rendered(state)

                    # Handle input with longer timeout for stability
                    key = term_input.get_key(timeout=0.2)
                    if key:
                        state, should_quit = handle_key(state, key, console)
                        if should_quit:
                            break
                        # Force immediate render after key press
                        state.refresh_controller.force_render()
                        live.update(render_layout(state))
                        state.refresh_controller.mark_rendered(state)

    except KeyboardInterrupt:
        pass
    finally:
        # Stop daemons if running
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        if state.researcher_daemon and state.researcher_daemon.running:
            loop.run_until_complete(state.researcher_daemon.stop())

        if state.teacher_daemon and state.teacher_daemon.running:
            loop.run_until_complete(state.teacher_daemon.stop())

        console.print("\n[cyan]Goodbye from Orson![/cyan]")


if __name__ == "__main__":
    main()
