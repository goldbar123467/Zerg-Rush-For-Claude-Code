"""
Orson CLI TUI Layout - Rich-based terminal interface

This module provides the visual layout structure for the Orson CLI,
a Midwestern-themed terminal UI for the Zerg Swarm agent system.

The layout mimics a small Indiana town with buildings representing
different system components (KERNEL, ML, QUANT, DEX, INTEGRATION).
"""

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Building definitions matching the web UI
BUILDINGS = {
    "town_hall": {"name": "Town Hall", "lane": None, "icon": "🏛️", "desc": "Mayor's Office - Wave Control"},
    "silo": {"name": "Grain Silo", "lane": "KERNEL", "icon": "🏭", "desc": "GPU Processing - CUDA/Triton"},
    "library": {"name": "Public Library", "lane": "ML", "icon": "📚", "desc": "Model Storage - Training/Inference"},
    "bank": {"name": "First National Bank", "lane": "QUANT", "icon": "🏦", "desc": "Strategy Vault - Backtests/Signals"},
    "gas_station": {"name": "Gas-N-Sip", "lane": "DEX", "icon": "⛽", "desc": "Fuel Station - Solana/Jupiter"},
    "post_office": {"name": "Post Office", "lane": None, "icon": "📮", "desc": "Mail Room - INBOX/OUTBOX"},
    "church": {"name": "Community Church", "lane": "INTEGRATION", "icon": "⛪", "desc": "Bringing It Together - CLI/Config"},
}

# Status icons for workers/tasks
STATUS_ICONS = {
    "done": "✅",
    "partial": "🔶",
    "blocked": "❌",
    "failed": "💀",
    "in_progress": "🔄",
    "pending": "⏳",
}


def make_layout() -> Layout:
    """
    Create the main TUI layout structure.

    Returns a Layout object with the following sections:
    - header: "ORSON, INDIANA" banner with wave/worker stats
    - buildings: Town buildings representing system lanes
    - main_street: Decorative road divider
    - lower_row: Post Office and Church
    - cemetery: Completed workers display
    - composer: Wave draft display
    - radio: Event log ticker
    """
    layout = Layout(name="root")

    # Main vertical split
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="buildings", size=9),
        Layout(name="main_street", size=3),
        Layout(name="lower_row", size=7),
        Layout(name="cemetery", size=6),
        Layout(name="composer", size=5),
        Layout(name="radio", size=3),
    )

    # Buildings row - 5 columns for the main buildings
    layout["buildings"].split_row(
        Layout(name="town_hall"),
        Layout(name="silo"),
        Layout(name="library"),
        Layout(name="bank"),
        Layout(name="gas_station"),
    )

    # Lower row - Post Office and Church
    layout["lower_row"].split_row(
        Layout(name="post_office", ratio=1),
        Layout(name="church", ratio=1),
    )

    return layout


def render_header(state: dict) -> Panel:
    """
    Render the header banner with wave/worker statistics.

    Args:
        state: Dict with keys: wave, workers, pending_tasks, completed_tasks

    Returns:
        Panel containing the header display
    """
    wave = state.get("wave", 0)
    workers = state.get("workers", [])
    pending = len(state.get("pending_tasks", []))
    completed = len(state.get("completed_tasks", []))
    active_count = len(workers)

    # Build the header text
    header_text = Text()

    # Banner line with corn
    header_text.append("🌽🌽🌽 ", style="yellow")
    header_text.append("ORSON, INDIANA", style="bold red on white")
    header_text.append(" 🌽🌽🌽\n", style="yellow")

    # MCP connection status
    mcp_connected = state.get("mcp_connected", False)
    mcp_status = "🟢" if mcp_connected else "🔴"

    # Stats line
    header_text.append(f"  {mcp_status} ", style="")
    header_text.append(f"Wave: ", style="dim")
    header_text.append(f"{wave}", style="bold cyan")
    header_text.append(f"  |  Workers: ", style="dim")
    header_text.append(f"{active_count}", style="bold green")
    header_text.append(f"  |  Pending: ", style="dim")
    header_text.append(f"{pending}", style="bold yellow")
    header_text.append(f"  |  Done: ", style="dim")
    header_text.append(f"{completed}", style="bold magenta")

    return Panel(
        header_text,
        border_style="bright_red",
        title="[bold white]THE HIVE WEARS FLANNEL[/bold white]",
        title_align="center",
    )


def _render_building(building_key: str, state: dict) -> Panel:
    """
    Render a single building panel.

    Args:
        building_key: Key from BUILDINGS dict
        state: Current state dict

    Returns:
        Panel for the building
    """
    building = BUILDINGS[building_key]
    lane = building["lane"]
    workers = state.get("workers", [])

    # Count workers assigned to this lane
    lane_workers = [w for w in workers if w.get("lane") == lane] if lane else []
    worker_count = len(lane_workers)

    # Build the display
    content = Text()
    content.append(f"{building['icon']}\n", style="bold")
    content.append(f"{building['name']}\n", style="bold white")

    if lane:
        content.append(f"[{lane}]\n", style="cyan dim")
        content.append(f"Workers: {worker_count}", style="green" if worker_count > 0 else "dim")
    else:
        content.append(f"{building['desc']}\n", style="dim italic")

    # Determine border color based on lane activity
    border_style = "dim white"
    if lane and worker_count > 0:
        border_style = "green"
    elif building_key == "town_hall":
        border_style = "red"
    elif building_key == "post_office":
        border_style = "blue"

    return Panel(
        content,
        border_style=border_style,
        title_align="center",
    )


def render_buildings(state: dict) -> Table:
    """
    Render the buildings row as a table.

    This is used when rendering individually is not needed.
    For the layout, use _render_building for each section.

    Args:
        state: Current state dict

    Returns:
        Table containing all buildings
    """
    table = Table(show_header=False, box=None, expand=True, padding=(0, 1))

    # Add columns for each building
    for _ in range(5):
        table.add_column(ratio=1, justify="center")

    # Create building panels
    town_hall = _render_building("town_hall", state)
    silo = _render_building("silo", state)
    library = _render_building("library", state)
    bank = _render_building("bank", state)
    gas_station = _render_building("gas_station", state)

    table.add_row(town_hall, silo, library, bank, gas_station)

    return table


def render_main_street() -> Panel:
    """
    Render the Main Street divider.

    Returns:
        Panel with the road decoration
    """
    road = Text()
    road.append("=" * 20, style="dim yellow")
    road.append(" MAIN STREET ", style="bold white on black")
    road.append("=" * 20, style="dim yellow")

    return Panel(
        road,
        border_style="dim black",
        style="on grey15",
    )


def render_lower_row(state: dict) -> Table:
    """
    Render the lower row with Post Office and Church.

    Args:
        state: Current state dict

    Returns:
        Table containing post office and church panels
    """
    table = Table(show_header=False, box=None, expand=True, padding=(0, 1))
    table.add_column(ratio=1, justify="center")
    table.add_column(ratio=1, justify="center")

    post_office = _render_building("post_office", state)
    church = _render_building("church", state)

    table.add_row(post_office, church)

    return table


def render_cemetery(state: dict) -> Panel:
    """
    Render the cemetery showing completed workers with status icons.

    Args:
        state: Dict with completed_tasks list containing dicts with
               'id', 'status', and optionally 'worker' keys

    Returns:
        Panel displaying completed worker tombstones
    """
    completed = state.get("completed_tasks", [])

    if not completed:
        content = Text("No workers have departed yet...", style="dim italic")
    else:
        content = Text()
        content.append("🪦 Peaceful Acres Memorial 🪦\n\n", style="bold white")

        # Display up to 10 most recent completed tasks
        recent = completed[-10:] if len(completed) > 10 else completed
        for task in recent:
            task_id = task.get("id", "???")
            status = task.get("status", "done").lower()
            worker = task.get("worker", "Unknown")

            icon = STATUS_ICONS.get(status, "⬜")

            # Style based on status
            if status == "done":
                style = "green"
            elif status == "partial":
                style = "yellow"
            elif status in ("blocked", "failed"):
                style = "red"
            else:
                style = "white"

            content.append(f"{icon} ", style=style)
            content.append(f"{task_id}", style=f"bold {style}")
            content.append(f" ({worker}) ", style="dim")

        if len(completed) > 10:
            content.append(f"\n... and {len(completed) - 10} more at rest", style="dim italic")

    return Panel(
        content,
        border_style="dim green",
        title="[bold green]🪦 CEMETERY[/bold green]",
        title_align="left",
    )


def render_composer(state: dict) -> Panel:
    """
    Render the wave composer showing draft tasks.

    Args:
        state: Dict with draft_tasks list containing task dicts

    Returns:
        Panel showing the current wave draft
    """
    draft_tasks = state.get("draft_tasks", [])
    wave = state.get("wave", 0)

    content = Text()
    content.append(f"Wave {wave + 1} Draft", style="bold cyan")
    content.append(f" ({len(draft_tasks)}/5 tasks)\n", style="dim")

    if not draft_tasks:
        content.append("No tasks queued. Press [a] to add tasks.", style="dim italic")
    else:
        for i, task in enumerate(draft_tasks[:5], 1):
            task_id = task.get("id", f"T{i:03d}")
            task_type = task.get("type", "UNKNOWN")
            lane = task.get("lane", "?")

            content.append(f"\n  {i}. ", style="dim")
            content.append(f"[{lane}] ", style="cyan")
            content.append(f"{task_id}", style="bold yellow")
            content.append(f" - {task_type}", style="white")

    return Panel(
        content,
        border_style="cyan",
        title="[bold cyan]🎼 WAVE COMPOSER[/bold cyan]",
        title_align="left",
    )


def render_radio(events: list) -> Panel:
    """
    Render the radio event log at the bottom.

    Args:
        events: List of event strings (most recent last)

    Returns:
        Panel showing the event ticker
    """
    if not events:
        ticker_text = Text("📻 Tuning in to WORM-FM... The voice of Orson.", style="dim italic")
    else:
        # Show the most recent event
        latest = events[-1] if events else ""
        ticker_text = Text()
        ticker_text.append("📻 ", style="bold yellow")
        ticker_text.append(latest, style="white")

    return Panel(
        ticker_text,
        border_style="yellow",
        title="[bold yellow]📻 WORM-FM RADIO[/bold yellow]",
        title_align="left",
        style="on grey7",
    )


def render_full_layout(state: dict) -> Layout:
    """
    Render the complete TUI layout with all sections populated.

    Args:
        state: Dict with keys:
            - wave: int
            - workers: list of worker dicts
            - pending_tasks: list of pending task dicts
            - completed_tasks: list of completed task dicts
            - draft_tasks: list of draft task dicts
            - events: list of event strings

    Returns:
        Fully populated Layout object ready for display
    """
    layout = make_layout()

    # Populate sections
    layout["header"].update(render_header(state))

    # Individual buildings
    layout["town_hall"].update(_render_building("town_hall", state))
    layout["silo"].update(_render_building("silo", state))
    layout["library"].update(_render_building("library", state))
    layout["bank"].update(_render_building("bank", state))
    layout["gas_station"].update(_render_building("gas_station", state))

    # Main street divider
    layout["main_street"].update(render_main_street())

    # Lower buildings
    layout["post_office"].update(_render_building("post_office", state))
    layout["church"].update(_render_building("church", state))

    # Cemetery and composer
    layout["cemetery"].update(render_cemetery(state))
    layout["composer"].update(render_composer(state))

    # Radio events
    events = state.get("events", [])
    layout["radio"].update(render_radio(events))

    return layout


# Convenience function to create a demo state for testing
def get_demo_state() -> dict:
    """
    Return a demo state dict for testing the TUI layout.

    Returns:
        Dict with sample data for all state fields
    """
    return {
        "wave": 3,
        "workers": [
            {"name": "BlueLake", "lane": "KERNEL", "task": "K001", "progress": 0.6},
            {"name": "RedMountain", "lane": "ML", "task": "M002", "progress": 0.3},
            {"name": "GreenValley", "lane": "QUANT", "task": "Q001", "progress": 0.9},
        ],
        "pending_tasks": [
            {"id": "K002", "lane": "KERNEL", "type": "ADD_PURE_FN"},
            {"id": "M003", "lane": "ML", "type": "ADD_TEST"},
        ],
        "completed_tasks": [
            {"id": "K001", "status": "done", "worker": "PurpleHill"},
            {"id": "M001", "status": "done", "worker": "OrangeSky"},
            {"id": "D001", "status": "partial", "worker": "YellowRiver"},
            {"id": "INT-001", "status": "blocked", "worker": "WhiteCloud"},
        ],
        "draft_tasks": [
            {"id": "K003", "lane": "KERNEL", "type": "ADD_STUB"},
            {"id": "M004", "lane": "ML", "type": "ADD_BENCH"},
        ],
        "events": [
            "Wave 2 complete. 4 tasks finished.",
            "BlueLake spawned at Grain Silo.",
            "RedMountain picked up M002.",
            "GreenValley almost done with Q001!",
        ],
    }
