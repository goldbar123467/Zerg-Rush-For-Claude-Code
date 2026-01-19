"""
Orson Spawner - Real Worker Spawning via tmux

Spawns actual Claude Code terminals in tmux sessions to execute tasks.
Each worker gets:
- A dedicated tmux session (worker-{name})
- A Claude CLI invocation with task prompt
- 4-minute TTL monitoring
- Output capture for result collection

"Earl's heading to work. He'll be back for supper."
"""

import asyncio
import subprocess
import os
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Callable
import shlex

from .state import generate_worker_name, generate_short_name, WORKER_TTL_MINUTES


# Worker output directory
WORKER_OUTPUT_DIR = Path("/tmp/orson-workers")


@dataclass
class SpawnedWorker:
    """A worker spawned in a tmux session."""
    name: str
    session_name: str
    task_id: str
    lane: str
    task_type: str
    objective: str
    spawned_at: datetime
    ttl_minutes: int = WORKER_TTL_MINUTES
    pid: Optional[int] = None
    output_file: Optional[Path] = None
    status: str = "running"  # running, done, partial, blocked, timeout, failed
    exit_code: Optional[int] = None
    injected_knowledge: Optional[str] = None

    @property
    def time_remaining(self) -> timedelta:
        """Get remaining time before TTL expires."""
        elapsed = datetime.now() - self.spawned_at
        ttl = timedelta(minutes=self.ttl_minutes)
        remaining = ttl - elapsed
        return max(timedelta(0), remaining)

    @property
    def is_expired(self) -> bool:
        """Check if worker has exceeded TTL."""
        return self.time_remaining.total_seconds() <= 0

    @property
    def progress(self) -> float:
        """Get progress as 0-1 based on TTL."""
        elapsed = datetime.now() - self.spawned_at
        ttl = timedelta(minutes=self.ttl_minutes)
        return min(1.0, elapsed.total_seconds() / ttl.total_seconds())


@dataclass
class SpawnerState:
    """State for the spawner system."""
    active_workers: List[SpawnedWorker] = field(default_factory=list)
    completed_workers: List[SpawnedWorker] = field(default_factory=list)
    wave: int = 0
    last_spawn: Optional[datetime] = None
    tmux_available: bool = True


def check_tmux_available() -> bool:
    """Check if tmux is available."""
    try:
        result = subprocess.run(
            ["tmux", "-V"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_claude_available() -> bool:
    """Check if Claude CLI is available."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_active_tmux_sessions() -> List[str]:
    """Get list of active tmux session names."""
    try:
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return [s.strip() for s in result.stdout.strip().split("\n") if s.strip()]
    except subprocess.SubprocessError:
        pass
    return []


def kill_tmux_session(session_name: str) -> bool:
    """Kill a tmux session."""
    try:
        result = subprocess.run(
            ["tmux", "kill-session", "-t", session_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def generate_task_prompt(task: dict, swarm_root: Path) -> str:
    """Generate the Claude CLI prompt for a task.

    Args:
        task: Task dict with id, lane, type, objective, and optional injected_knowledge
        swarm_root: Path to SWARM directory

    Returns:
        Prompt string for Claude CLI
    """
    task_id = task.get("id", "UNKNOWN")
    lane = task.get("lane", "KERNEL")
    task_type = task.get("type", "TASK")
    objective = task.get("objective", "")
    knowledge = task.get("injected_knowledge", "")

    # Build the prompt
    prompt_parts = [
        f"You are a Zergling worker executing task {task_id}.",
        f"Lane: {lane}",
        f"Type: {task_type}",
        "",
        "HARD CONSTRAINTS (NON-NEGOTIABLE):",
        "- Maximum 4 minutes (hard stop)",
        "- Maximum 100 new lines of code",
        "- Touch at most 2 files (1 main + 1 test/doc)",
        "- NO new dependencies",
        "- NO architectural decisions",
        "- NO refactors outside the task",
        "",
        f"OBJECTIVE: {objective}",
    ]

    if knowledge:
        prompt_parts.extend([
            "",
            "RELEVANT KNOWLEDGE FROM RAG:",
            knowledge,
        ])

    # Add task file context if exists
    task_file = swarm_root / "TASKS" / lane / f"{task_id}.md"
    if task_file.exists():
        prompt_parts.extend([
            "",
            f"Task file: {task_file}",
            "Read the task file for full context before starting.",
        ])

    prompt_parts.extend([
        "",
        "When done, create a result file at:",
        f"  {swarm_root}/INBOX/{task_id}_RESULT.md",
        "",
        "Result format:",
        "| Status | DONE/PARTIAL/BLOCKED |",
        "| Lines | <count> |",
        "",
        "Then exit immediately. Do not wait for further instructions.",
    ])

    return "\n".join(prompt_parts)


def spawn_worker(
    task: dict,
    swarm_root: Path,
    wave: int,
    worker_name: Optional[str] = None
) -> Optional[SpawnedWorker]:
    """Spawn a worker in a tmux session to execute a task.

    Args:
        task: Task dict with id, lane, type, objective
        swarm_root: Path to SWARM directory
        wave: Current wave number
        worker_name: Optional worker name (generates one if not provided)

    Returns:
        SpawnedWorker if successful, None otherwise
    """
    # Ensure output directory exists
    WORKER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate worker name
    if not worker_name:
        worker_name = generate_short_name()

    task_id = task.get("id", "UNKNOWN")
    lane = task.get("lane", "KERNEL")
    task_type = task.get("type", "TASK")
    objective = task.get("objective", "")

    # Create unique session name
    session_name = f"worker-{worker_name.lower().replace(' ', '-')}-{task_id}"

    # Check if session already exists
    active_sessions = get_active_tmux_sessions()
    if session_name in active_sessions:
        # Session already exists, kill it first
        kill_tmux_session(session_name)

    # Output file for capturing results
    output_file = WORKER_OUTPUT_DIR / f"{session_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

    # Generate the prompt
    prompt = generate_task_prompt(task, swarm_root)

    # Build Claude CLI command
    # Use --print to output to stdout, redirect to file
    # Use --dangerously-skip-permissions to avoid prompts in automated context
    claude_cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        prompt
    ]

    # Escape for shell
    claude_cmd_str = " ".join(shlex.quote(arg) for arg in claude_cmd)

    # Full command with output capture and exit
    # The command: runs claude, captures output, then exits
    full_cmd = f"{claude_cmd_str} 2>&1 | tee {shlex.quote(str(output_file))}; exit"

    # Spawn tmux session
    try:
        result = subprocess.run(
            [
                "tmux", "new-session",
                "-d",  # Detached
                "-s", session_name,  # Session name
                "-c", str(swarm_root.parent),  # Working directory (project root)
                "bash", "-c", full_cmd
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return None

        # Create worker record
        worker = SpawnedWorker(
            name=worker_name,
            session_name=session_name,
            task_id=task_id,
            lane=lane,
            task_type=task_type,
            objective=objective,
            spawned_at=datetime.now(),
            output_file=output_file,
            injected_knowledge=task.get("injected_knowledge")
        )

        return worker

    except subprocess.SubprocessError:
        return None


def check_worker_status(worker: SpawnedWorker) -> SpawnedWorker:
    """Check the status of a spawned worker.

    Updates worker status based on:
    - tmux session existence
    - TTL expiration
    - Output file contents

    Args:
        worker: The worker to check

    Returns:
        Updated worker
    """
    # Check if session still exists
    active_sessions = get_active_tmux_sessions()
    session_alive = worker.session_name in active_sessions

    if not session_alive:
        # Session ended - determine final status
        if worker.status == "running":
            # Check output file for status
            if worker.output_file and worker.output_file.exists():
                try:
                    content = worker.output_file.read_text()
                    # Look for status in output
                    if "| Status | DONE" in content or "Status: DONE" in content:
                        worker.status = "done"
                    elif "| Status | PARTIAL" in content or "Status: PARTIAL" in content:
                        worker.status = "partial"
                    elif "| Status | BLOCKED" in content or "Status: BLOCKED" in content:
                        worker.status = "blocked"
                    else:
                        # Default to done if session completed without explicit status
                        worker.status = "done"
                except IOError:
                    worker.status = "failed"
            else:
                worker.status = "failed"

    elif worker.is_expired:
        # TTL expired - kill the session
        kill_tmux_session(worker.session_name)
        worker.status = "timeout"

    return worker


def spawn_wave(
    tasks: List[dict],
    swarm_root: Path,
    wave: int,
    state: Optional[SpawnerState] = None
) -> SpawnerState:
    """Spawn a wave of workers.

    Args:
        tasks: List of task dicts to spawn workers for
        swarm_root: Path to SWARM directory
        wave: Wave number
        state: Optional existing state to update

    Returns:
        Updated SpawnerState
    """
    if state is None:
        state = SpawnerState()

    state.wave = wave
    state.last_spawn = datetime.now()

    for task in tasks:
        worker = spawn_worker(task, swarm_root, wave)
        if worker:
            state.active_workers.append(worker)

    return state


def collect_completed(state: SpawnerState) -> SpawnerState:
    """Collect completed workers and update state.

    Checks all active workers, moves completed ones to completed list.

    Args:
        state: Current spawner state

    Returns:
        Updated state
    """
    still_active = []

    for worker in state.active_workers:
        worker = check_worker_status(worker)

        if worker.status in ("running",):
            still_active.append(worker)
        else:
            state.completed_workers.append(worker)

    state.active_workers = still_active
    return state


def kill_all_workers(state: SpawnerState) -> SpawnerState:
    """Kill all active workers.

    Args:
        state: Current spawner state

    Returns:
        Updated state with all workers killed
    """
    for worker in state.active_workers:
        kill_tmux_session(worker.session_name)
        worker.status = "killed"
        state.completed_workers.append(worker)

    state.active_workers = []
    return state


def get_worker_output(worker: SpawnedWorker) -> str:
    """Get the output from a worker's log file.

    Args:
        worker: The worker to get output from

    Returns:
        Output content or empty string
    """
    if worker.output_file and worker.output_file.exists():
        try:
            return worker.output_file.read_text()
        except IOError:
            pass
    return ""


def parse_worker_result(output: str) -> tuple:
    """Parse worker output for status line.

    Looks for status patterns in the output:
    - DONE: task_id - message
    - PARTIAL: task_id - message
    - BLOCKED: task_id - message
    - | Status | DONE/PARTIAL/BLOCKED |
    - Status: DONE/PARTIAL/BLOCKED

    Args:
        output: The worker's output text

    Returns:
        Tuple of (status, task_id, message, lines_written)
    """
    import re

    status = "UNKNOWN"
    task_id = ""
    message = "No status line found in output"
    lines_written = 0

    # Try to extract lines count from output
    lines_match = re.search(r'\| Lines \| (\d+) \|', output)
    if lines_match:
        lines_written = int(lines_match.group(1))

    # Alternative lines format
    lines_match2 = re.search(r'Lines:\s*(\d+)', output)
    if lines_match2:
        lines_written = int(lines_match2.group(1))

    # Check for explicit status line patterns
    for line in output.split('\n'):
        line = line.strip()

        # Pattern: "DONE: K001 - added jwt_validate function"
        done_match = re.match(r'^DONE:\s*(\w+)\s*[-–]\s*(.+)$', line)
        if done_match:
            status = "DONE"
            task_id = done_match.group(1)
            message = done_match.group(2).strip()
            break

        partial_match = re.match(r'^PARTIAL:\s*(\w+)\s*[-–]\s*(.+)$', line)
        if partial_match:
            status = "PARTIAL"
            task_id = partial_match.group(1)
            message = partial_match.group(2).strip()
            break

        blocked_match = re.match(r'^BLOCKED:\s*(\w+)\s*[-–]\s*(.+)$', line)
        if blocked_match:
            status = "BLOCKED"
            task_id = blocked_match.group(1)
            message = blocked_match.group(2).strip()
            break

        # Pattern: "| Status | DONE |"
        table_match = re.match(r'\|\s*Status\s*\|\s*(DONE|PARTIAL|BLOCKED)\s*\|', line)
        if table_match:
            status = table_match.group(1)
            message = f"Task completed with status {status}"
            break

        # Pattern: "Status: DONE"
        colon_match = re.match(r'^Status:\s*(DONE|PARTIAL|BLOCKED)', line)
        if colon_match:
            status = colon_match.group(1)
            message = f"Task completed with status {status}"
            break

    # Try to extract task ID from output if not found
    if not task_id:
        task_match = re.search(r'task\s+([A-Z]+-?\d+|[A-Z]\d+)', output, re.IGNORECASE)
        if task_match:
            task_id = task_match.group(1).upper()

    # Extract a summary from output if no specific message
    if message == "No status line found in output" and status != "UNKNOWN":
        # Look for summary or result section
        summary_match = re.search(r'(?:Summary|Result|Output):\s*(.+?)(?:\n|$)', output, re.IGNORECASE)
        if summary_match:
            message = summary_match.group(1).strip()[:100]  # Limit length

    return (status, task_id, message, lines_written)


def cleanup_worker_session(worker: SpawnedWorker) -> bool:
    """Clean up a worker's tmux session.

    Args:
        worker: The worker to clean up

    Returns:
        True if cleanup successful
    """
    success = True

    # Kill tmux session if it exists
    if worker.session_name:
        active_sessions = get_active_tmux_sessions()
        if worker.session_name in active_sessions:
            success = kill_tmux_session(worker.session_name)

    return success


# Singleton state
_spawner_state: Optional[SpawnerState] = None


def get_spawner_state() -> SpawnerState:
    """Get or create the singleton spawner state."""
    global _spawner_state
    if _spawner_state is None:
        _spawner_state = SpawnerState()
        _spawner_state.tmux_available = check_tmux_available()
    return _spawner_state


def reset_spawner_state() -> SpawnerState:
    """Reset the spawner state."""
    global _spawner_state
    _spawner_state = SpawnerState()
    _spawner_state.tmux_available = check_tmux_available()
    return _spawner_state
