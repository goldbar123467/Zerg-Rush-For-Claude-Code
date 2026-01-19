"""
Brain Panel - RAG Brain Status Display

Shows memory tiers, model info, and top concepts from RAG Brain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from rich.panel import Panel
from rich.text import Text
from rich.table import Table


@dataclass
class BrainPanelState:
    """State for the brain panel."""
    visible: bool = False
    connected: bool = False
    stats: dict = field(default_factory=dict)
    concepts: list = field(default_factory=list)
    last_refresh: Optional[datetime] = None
    error: Optional[str] = None


def format_time_ago(dt: Optional[datetime]) -> str:
    """Format a datetime as time ago string."""
    if not dt:
        return "never"
    delta = datetime.now() - dt
    if delta.total_seconds() < 60:
        return "just now"
    elif delta.total_seconds() < 3600:
        mins = int(delta.total_seconds() / 60)
        return f"{mins}m ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = int(delta.total_seconds() / 86400)
        return f"{days}d ago"


def render_brain_panel(state: BrainPanelState) -> Panel:
    """
    Render the RAG Brain status panel.

    Args:
        state: BrainPanelState with stats and concepts

    Returns:
        Rich Panel with brain status display
    """
    content = Text()

    # Status indicator
    status_icon = "\u2705" if state.connected else "\u274c"
    status_text = "ONLINE" if state.connected else "OFFLINE"

    if state.error:
        content.append(f"Error: {state.error}\n\n", style="red")

    # Memory tiers section
    content.append("MEMORY TIERS:\n", style="bold cyan")

    stats = state.stats or {}
    tiers = stats.get("tiers", {})

    # Default tier counts if not available
    core = tiers.get("core", 0)
    active = tiers.get("active", 0)
    archive = tiers.get("archive", 0)
    quarantine = tiers.get("quarantine", 0)
    total = stats.get("total_memories", core + active + archive + quarantine)

    content.append("\u251c\u2500\u2500 Core:       ", style="dim")
    content.append(f"{core:,}", style="bold green")
    content.append(" memories\n")

    content.append("\u251c\u2500\u2500 Active:     ", style="dim")
    content.append(f"{active:,}", style="bold yellow")
    content.append(" memories\n")

    content.append("\u251c\u2500\u2500 Archive:    ", style="dim")
    content.append(f"{archive:,}", style="bold blue")
    content.append(" memories\n")

    content.append("\u2514\u2500\u2500 Quarantine: ", style="dim")
    content.append(f"{quarantine:,}", style="bold red")
    content.append(" memories\n\n")

    # Model info
    model_info = stats.get("model", {})
    model_version = model_info.get("version", "v1")
    last_trained = model_info.get("last_trained")
    f1_score = model_info.get("f1", 0.0)

    if last_trained:
        try:
            trained_dt = datetime.fromisoformat(last_trained)
            trained_ago = format_time_ago(trained_dt)
        except (ValueError, TypeError):
            trained_ago = str(last_trained)
    else:
        trained_ago = "never"

    content.append(f"MODEL: {model_version}", style="cyan")
    content.append(f" \u2502 Last trained: {trained_ago}", style="dim")
    content.append(f" \u2502 F1: {f1_score:.3f}\n\n", style="dim")

    # Top concepts
    content.append("TOP CONCEPTS:\n", style="bold cyan")

    concepts = state.concepts[:5] if state.concepts else []
    if concepts:
        for i, concept in enumerate(concepts):
            if isinstance(concept, dict):
                name = concept.get("name", concept.get("concept", "unknown"))
                count = concept.get("count", concept.get("memory_count", 0))
            else:
                name = str(concept)
                count = 0

            prefix = "\u2514\u2500\u2500" if i == len(concepts) - 1 else "\u251c\u2500\u2500"
            content.append(f"{prefix} ", style="dim")
            content.append(f"{name}", style="bold white")
            if count > 0:
                content.append(f" ({count} memories)", style="dim")
            content.append("\n")
    else:
        content.append("\u2514\u2500\u2500 (no concepts yet)\n", style="dim italic")

    content.append("\n")

    # Footer with controls
    content.append("[Q]", style="bold cyan")
    content.append("uery  ", style="dim")
    content.append("[R]", style="bold cyan")
    content.append("efresh", style="dim")
    content.append("                                     ", style="dim")
    content.append("[ESC]", style="bold yellow")
    content.append(" \u25c4\u2500\u2500", style="dim")

    # Last refresh time
    if state.last_refresh:
        refresh_text = f"\nLast refresh: {format_time_ago(state.last_refresh)}"
        content.append(refresh_text, style="dim italic")

    return Panel(
        content,
        title=f"\U0001f9e0 ORSON TOWN MEMORY                          STATUS: {status_icon} {status_text}",
        title_align="left",
        border_style="magenta" if state.connected else "red",
        width=70,
        height=20,
    )


def render_brain_status_indicator(connected: bool, stats: dict = None) -> Text:
    """
    Render a compact RAG status indicator for the header.

    Args:
        connected: Whether RAG Brain is connected
        stats: Optional stats dict with total_memories

    Returns:
        Rich Text with status indicator
    """
    text = Text()
    text.append("RAG: ", style="dim")

    if connected:
        text.append("\U0001f7e2", style="green")  # Green circle
        if stats:
            total = stats.get("total_memories", 0)
            if total > 0:
                text.append(f" {total:,}", style="dim")
    else:
        text.append("\U0001f534", style="red")  # Red circle

    return text
