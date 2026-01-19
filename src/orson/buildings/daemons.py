"""
Daemon Control Panel - Orson Services Management

Control panel for all background processes:
- Researcher (file watcher)
- Teacher (prompt updater)
- RAG Brain connection
- Zerg MCP connection

"The machinery that keeps the town running."
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Any
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

DAEMONS_ICON = "\u2699\ufe0f"  # Gear emoji


@dataclass
class DaemonConfig:
    """Configuration for daemon auto-start and settings."""
    researcher_autostart: bool = True
    teacher_autostart: bool = True
    researcher_watch_paths: List[str] = field(default_factory=lambda: ["./src", "./SWARM"])
    researcher_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.md"])
    researcher_poll_interval: float = 5.0
    teacher_interval: int = 300  # 5 minutes
    teacher_memories_per_lesson: int = 10


@dataclass
class DaemonPanelState:
    """State for the daemon control panel."""
    is_visible: bool = False
    config: DaemonConfig = field(default_factory=DaemonConfig)
    # Cached status info
    last_researcher_activity: Optional[str] = None
    last_teacher_activity: Optional[str] = None
    researcher_queue_depth: int = 0
    teacher_lessons_taught: int = 0


def format_time_ago(dt: Optional[datetime]) -> str:
    """Format a datetime as 'Xm ago' or 'Xs ago'."""
    if not dt:
        return "never"

    delta = datetime.now() - dt
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return f"{seconds}s ago"
    elif seconds < 3600:
        return f"{seconds // 60}m ago"
    elif seconds < 86400:
        return f"{seconds // 3600}h ago"
    else:
        return f"{seconds // 86400}d ago"


def render_daemons_panel(
    state: DaemonPanelState,
    researcher_daemon: Any = None,
    teacher_daemon: Any = None,
    rag_connected: bool = False,
    rag_stats: dict = None,
    mcp_connected: bool = False,
    wave: int = 0
) -> Panel:
    """
    Render the daemon control panel.

    Args:
        state: DaemonPanelState
        researcher_daemon: ResearcherDaemon instance or None
        teacher_daemon: TeacherDaemon instance or None
        rag_connected: Whether RAG Brain is connected
        rag_stats: RAG Brain statistics dict
        mcp_connected: Whether Zerg MCP is connected
        wave: Current wave number

    Returns:
        Rich Panel with daemon status
    """
    content = Text()

    # === DAEMON STATUS TABLE ===
    content.append("DAEMON STATUS:\n", style="bold cyan")

    status_table = Table(box=None, show_header=True, padding=(0, 1))
    status_table.add_column("Service", style="white")
    status_table.add_column("Status", justify="center")
    status_table.add_column("Last Activity", style="dim")

    # Researcher status
    researcher_running = researcher_daemon and researcher_daemon.running if researcher_daemon else False
    researcher_status = "\U0001f7e2 ON" if researcher_running else "\U0001f534 OFF"
    researcher_activity = "idle"
    if researcher_daemon and researcher_running:
        if researcher_daemon.files_processed > 0:
            researcher_activity = f"Processed {researcher_daemon.files_processed} files"
        elif researcher_daemon.queue.qsize() > 0:
            researcher_activity = f"Queue: {researcher_daemon.queue.qsize()}"
        else:
            researcher_activity = "Watching..."

    status_table.add_row(
        "\U0001f50d Researcher",
        Text(researcher_status, style="green" if researcher_running else "red"),
        researcher_activity
    )

    # Teacher status
    teacher_running = teacher_daemon and teacher_daemon.running if teacher_daemon else False
    teacher_status = "\U0001f7e2 ON" if teacher_running else "\U0001f534 OFF"
    teacher_activity = "idle"
    if teacher_daemon and teacher_running:
        if teacher_daemon.last_teach_time:
            teacher_activity = f"Taught {format_time_ago(teacher_daemon.last_teach_time)}"
        else:
            teacher_activity = "Waiting..."

    status_table.add_row(
        "\U0001f469\u200d\U0001f3eb Teacher",
        Text(teacher_status, style="green" if teacher_running else "red"),
        teacher_activity
    )

    # RAG Brain status
    rag_status = "\U0001f7e2 CONN" if rag_connected else "\U0001f534 DISC"
    rag_activity = "Not connected"
    if rag_connected and rag_stats:
        total_memories = rag_stats.get("total_memories", 0)
        rag_activity = f"{total_memories:,} memories"

    status_table.add_row(
        "\U0001f9e0 RAG Brain",
        Text(rag_status, style="green" if rag_connected else "red"),
        rag_activity
    )

    # Zerg MCP status
    mcp_status = "\U0001f7e2 CONN" if mcp_connected else "\U0001f534 DISC"
    mcp_activity = f"Wave {wave}" if mcp_connected else "Not connected"

    status_table.add_row(
        "\U0001f41d Zerg MCP",
        Text(mcp_status, style="green" if mcp_connected else "red"),
        mcp_activity
    )

    # Render table to text
    from io import StringIO
    from rich.console import Console
    buf = StringIO()
    temp_console = Console(file=buf, force_terminal=True, width=60)
    temp_console.print(status_table)
    content.append(buf.getvalue())

    content.append("\n")

    # === RESEARCHER CONFIG ===
    content.append("RESEARCHER CONFIG:\n", style="bold yellow")
    if researcher_daemon:
        watch_paths = ", ".join(str(p.name) if hasattr(p, 'name') else str(p)
                                for p in researcher_daemon.watch_paths[:3])
        if len(researcher_daemon.watch_paths) > 3:
            watch_paths += f" (+{len(researcher_daemon.watch_paths) - 3})"
        patterns = ", ".join(researcher_daemon.patterns[:3])
        poll = researcher_daemon.poll_interval
        queue = researcher_daemon.queue.qsize() if researcher_daemon.queue else 0

        content.append(f"\u251c\u2500\u2500 Watch paths: {watch_paths or 'none'}\n", style="dim")
        content.append(f"\u251c\u2500\u2500 File types: {patterns}\n", style="dim")
        content.append(f"\u251c\u2500\u2500 Poll interval: {poll}s\n", style="dim")
        content.append(f"\u2514\u2500\u2500 Queue depth: {queue} pending\n", style="dim")
    else:
        content.append("\u2514\u2500\u2500 Not initialized\n", style="dim")

    content.append("\n")

    # === TEACHER CONFIG ===
    content.append("TEACHER CONFIG:\n", style="bold magenta")
    if teacher_daemon:
        interval = int(teacher_daemon.lesson_interval / 60)
        lessons = teacher_daemon.lessons_taught
        last_time = format_time_ago(teacher_daemon.last_teach_time) if teacher_daemon.last_teach_time else "never"

        content.append(f"\u251c\u2500\u2500 Lesson interval: {interval} minutes\n", style="dim")
        content.append(f"\u251c\u2500\u2500 Lessons taught: {lessons}\n", style="dim")
        content.append(f"\u2514\u2500\u2500 Last full cycle: {last_time}\n", style="dim")
    else:
        content.append("\u2514\u2500\u2500 Not initialized\n", style="dim")

    content.append("\n")

    # === CONTROLS ===
    content.append("[R] Toggle Researcher  [T] Toggle Teacher  [L] Learn Now\n", style="bold white")
    content.append("                                            [ESC] Close", style="dim")

    return Panel(
        content,
        title=f"{DAEMONS_ICON} ORSON SERVICES",
        subtitle="Background Processes",
        border_style="blue"
    )


def get_daemon_summary(
    researcher_daemon: Any = None,
    teacher_daemon: Any = None,
    rag_connected: bool = False,
    mcp_connected: bool = False
) -> str:
    """
    Get a one-line summary of daemon status.

    Returns:
        String like "R:ON T:OFF RAG:OK MCP:OK"
    """
    r_status = "ON" if (researcher_daemon and researcher_daemon.running) else "OFF"
    t_status = "ON" if (teacher_daemon and teacher_daemon.running) else "OFF"
    rag_status = "OK" if rag_connected else "X"
    mcp_status = "OK" if mcp_connected else "X"

    return f"R:{r_status} T:{t_status} RAG:{rag_status} MCP:{mcp_status}"
