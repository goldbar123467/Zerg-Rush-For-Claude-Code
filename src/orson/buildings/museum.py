"""
Museum Building - The Data Vault

Displays wave history, worker statistics, and emerged concepts from RAG Brain.
"In Orson, we remember our own."
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import json

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

# Icons
MUSEUM_ICON = "\U0001f3db\ufe0f"  # Classical building
TAG_ICON = "\U0001f3f7\ufe0f"  # Label/tag
BRAIN_ICON = "\U0001f9e0"  # Brain


@dataclass
class WaveHistory:
    """Record of a completed wave."""
    wave_num: int
    started: datetime
    completed: datetime
    tasks_completed: int
    tasks_partial: int
    tasks_blocked: int
    total_lines: int


@dataclass
class WorkerStats:
    """Aggregate worker statistics."""
    total_spawned: int = 0
    total_completed: int = 0
    by_status: Dict[str, int] = field(default_factory=dict)
    by_lane: Dict[str, int] = field(default_factory=dict)
    total_lines_written: int = 0


@dataclass
class Concept:
    """A concept cluster from RAG Brain."""
    name: str
    memory_count: int
    sample_text: str = ""  # Sample memory text for preview


@dataclass
class MuseumState:
    """State for the museum display."""
    wave_history: List[WaveHistory] = field(default_factory=list)
    worker_stats: WorkerStats = field(default_factory=WorkerStats)
    is_visible: bool = False
    # RAG concepts
    concepts: List[Concept] = field(default_factory=list)
    rag_connected: bool = False
    # Concept detail view
    selected_concept_idx: int = -1  # -1 means no selection
    concept_memories: List[dict] = field(default_factory=list)  # Memories for selected concept
    show_concept_detail: bool = False


def render_concept_detail(state: MuseumState) -> Panel:
    """Render the detail view for a selected concept."""
    content = Text()

    if state.selected_concept_idx < 0 or state.selected_concept_idx >= len(state.concepts):
        content.append("No concept selected", style="dim")
        return Panel(content, title="Concept Detail", border_style="cyan")

    concept = state.concepts[state.selected_concept_idx]
    content.append(f"{TAG_ICON} {concept.name}\n", style="bold magenta")
    content.append(f"   {concept.memory_count} memories\n\n", style="dim")

    content.append("RELATED MEMORIES:\n", style="bold cyan")
    content.append("\u2500" * 50 + "\n", style="dim")

    if state.concept_memories:
        for i, memory in enumerate(state.concept_memories[:10], 1):
            if isinstance(memory, dict):
                mem_content = memory.get("content", memory.get("text", str(memory)))
                quality = memory.get("quality", 0.5)
            else:
                mem_content = str(memory)
                quality = 0.5

            # Quality indicator
            if quality >= 0.7:
                q_icon = "\U0001f7e2"
            elif quality >= 0.4:
                q_icon = "\U0001f7e1"
            else:
                q_icon = "\U0001f534"

            # Truncate long content
            if len(mem_content) > 70:
                mem_content = mem_content[:67] + "..."

            content.append(f"{i}. {q_icon} ", style="dim")
            content.append(f"{mem_content}\n", style="white")
    else:
        content.append("(No memories found for this concept)\n", style="dim italic")

    content.append("\n[ESC]", style="bold yellow")
    content.append(" Back to Museum", style="dim")

    return Panel(
        content,
        title=f"{BRAIN_ICON} CONCEPT: {concept.name}",
        border_style="cyan",
        width=70,
        height=20
    )


def render_museum(state: MuseumState, width: int = 70) -> Panel:
    """Render the museum panel with wave history and emerged concepts."""
    # If showing concept detail, render that instead
    if state.show_concept_detail:
        return render_concept_detail(state)

    content = Text()

    # Two-column layout: Wave History | Emerged Concepts
    # Build left column (Wave History)
    left_col = Text()
    left_col.append("WAVE HISTORY:\n", style="bold cyan")

    if state.wave_history:
        for wave in state.wave_history[-7:]:  # Show last 7 waves
            total = wave.tasks_completed + wave.tasks_partial + wave.tasks_blocked
            if wave.tasks_blocked == 0 and wave.tasks_partial == 0:
                status_icon = "\u2705"  # Green check
            elif wave.tasks_blocked > 0:
                status_icon = "\u274c"  # Red X
            else:
                status_icon = "\u26a0\ufe0f"  # Warning

            left_col.append(f"Wave {wave.wave_num}: ", style="yellow")
            left_col.append(f"{wave.tasks_completed}/{total} ", style="green")
            left_col.append(f"{status_icon}\n")
    else:
        # Show from worker stats if no wave history
        stats = state.worker_stats
        if stats.total_completed > 0:
            left_col.append(f"Completed: {stats.total_completed}\n", style="green")
            if stats.by_status:
                for status, count in stats.by_status.items():
                    style = {"DONE": "green", "PARTIAL": "magenta", "BLOCKED": "red"}.get(status, "white")
                    left_col.append(f"  {status}: {count}\n", style=style)
        else:
            left_col.append("No wave history yet\n", style="dim italic")

    # Build right column (Emerged Concepts)
    right_col = Text()
    right_col.append("EMERGED CONCEPTS:", style="bold cyan")
    if state.rag_connected:
        right_col.append(" \U0001f7e2\n", style="green")
    else:
        right_col.append(" \U0001f534\n", style="red")

    if state.concepts:
        for i, concept in enumerate(state.concepts[:7]):
            # Selection marker
            if i == state.selected_concept_idx:
                marker = "\u25b6 "
                style = "bold magenta"
            else:
                marker = "  "
                style = "white"

            right_col.append(f"{marker}{TAG_ICON} ", style="dim")
            right_col.append(f"{concept.name}", style=style)
            right_col.append(f" ({concept.memory_count})\n", style="dim")

            # Show sample text if available
            if concept.sample_text:
                sample = concept.sample_text[:35] + "..." if len(concept.sample_text) > 35 else concept.sample_text
                right_col.append(f"     \u2514\u2500 \"{sample}\"\n", style="dim italic")
    else:
        right_col.append("(No concepts yet)\n", style="dim italic")
        right_col.append("Store memories to see\n", style="dim")
        right_col.append("emerging patterns.\n", style="dim")

    # Combine columns
    content.append(left_col)
    content.append("\n")
    content.append("\u2500" * 30 + "\n", style="dim")
    content.append(right_col)

    # Footer with controls
    content.append("\n")
    content.append("[UP/DOWN]", style="bold cyan")
    content.append("=Select  ", style="dim")
    content.append("[ENTER]", style="bold cyan")
    content.append("=View  ", style="dim")
    content.append("[R]", style="bold cyan")
    content.append("=Refresh  ", style="dim")
    content.append("[ESC]", style="bold yellow")
    content.append("=Close", style="dim")

    return Panel(
        content,
        title=f"{MUSEUM_ICON} ORSON HISTORICAL SOCIETY",
        border_style="magenta",
        width=width,
        height=24
    )


async def fetch_concepts(rag_client) -> List[Concept]:
    """Fetch concept clusters from RAG Brain.

    Args:
        rag_client: RAGClient instance

    Returns:
        List of Concept objects
    """
    raw_concepts = await rag_client.concepts()
    concepts = []
    for c in raw_concepts:
        if isinstance(c, dict):
            name = c.get("name", c.get("concept", str(c)))
            count = c.get("memory_count", c.get("count", 0))
            sample = c.get("sample_text", c.get("sample", ""))
        else:
            name = str(c)
            count = 0
            sample = ""
        concepts.append(Concept(name=name, memory_count=count, sample_text=sample))
    return concepts


async def fetch_concept_memories(concept_name: str, rag_client, limit: int = 10) -> List[dict]:
    """Fetch memories related to a specific concept.

    Args:
        concept_name: The concept to query
        rag_client: RAGClient instance
        limit: Max memories to return

    Returns:
        List of memory dicts
    """
    memories = await rag_client.recall(concept_name, limit=limit)
    return memories


def refresh_museum_concepts(state: MuseumState) -> MuseumState:
    """Refresh RAG concepts for museum display (sync wrapper)."""
    from ..rag_client import get_rag_client
    rag_client = get_rag_client()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def _fetch():
        connected = await rag_client.health()
        if not connected:
            return False, []
        concepts = await fetch_concepts(rag_client)
        return True, concepts

    try:
        connected, concepts = loop.run_until_complete(_fetch())
        state.rag_connected = connected
        state.concepts = concepts
    except Exception:
        state.rag_connected = False

    return state


def load_concept_memories(state: MuseumState) -> MuseumState:
    """Load memories for the currently selected concept (sync wrapper)."""
    if state.selected_concept_idx < 0 or state.selected_concept_idx >= len(state.concepts):
        return state

    from ..rag_client import get_rag_client
    rag_client = get_rag_client()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    concept = state.concepts[state.selected_concept_idx]
    try:
        memories = loop.run_until_complete(fetch_concept_memories(concept.name, rag_client))
        state.concept_memories = memories
    except Exception:
        state.concept_memories = []

    return state


def load_museum_data(swarm_root: Path) -> MuseumState:
    """Load historical data from SWARM/ARCHIVE and STATE.json."""
    state = MuseumState()
    state_file = swarm_root / "STATE.json"

    if state_file.exists():
        try:
            with open(state_file) as f:
                data = json.load(f)

            completed = data.get("completed_tasks", [])
            state.worker_stats.total_completed = len(completed)
            state.worker_stats.total_spawned = len(completed) + len(data.get("active_zerglings", []))

            # Count by status from completed tasks
            for task_id in completed:
                state.worker_stats.by_status["DONE"] = state.worker_stats.by_status.get("DONE", 0) + 1

        except (json.JSONDecodeError, IOError):
            pass

    # Fetch RAG concepts
    state = refresh_museum_concepts(state)

    return state
