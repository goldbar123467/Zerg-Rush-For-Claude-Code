"""
School Building - Training Center

Displays curricula, prompt versions, and pre-spawn knowledge from RAG Brain.
"Education is the foundation of a good hive."
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

SCHOOL_ICON = "\U0001f3eb"  # School building emoji
BOOK_ICON = "\U0001f4d6"  # Open book
GRAD_ICON = "\U0001f393"  # Graduation cap
BRAIN_ICON = "\U0001f9e0"  # Brain
INJECT_ICON = "\U0001f489"  # Syringe (injection)

TASK_TYPES = {
    "ADD_STUB": "Skeleton + TODOs",
    "ADD_PURE_FN": "One function + doc",
    "ADD_TEST": "1-3 test cases",
    "FIX_ONE_BUG": "Single bug fix",
    "ADD_ASSERTS": "Runtime checks",
    "ADD_METRIC": "One metric + log",
    "ADD_BENCH": "Benchmark snippet",
    "DOC_SNIPPET": "Doc section",
    "REFACTOR_TINY": "Rename/move only"
}

LANE_PROMPTS = {
    "KERNEL": "Correctness first. Keep changes minimal.",
    "ML": "No dataset changes unless asked. Add smoke test.",
    "QUANT": "No lookahead. Add sanity check.",
    "DEX": "Safety checks > speed. Never remove guardrails.",
    "INTEGRATION": "Glue only. No domain logic. Max 3 files."
}


@dataclass
class SchoolState:
    """State for school display."""
    prompts_content: str = ""
    selected_lane: str = "KERNEL"
    is_visible: bool = False
    # RAG knowledge for pre-spawn injection
    lane_knowledge: Dict[str, List[dict]] = field(default_factory=dict)
    last_knowledge_fetch: Optional[datetime] = None
    rag_connected: bool = False


def load_prompts(swarm_root: Path) -> str:
    """Load PROMPTS.md content."""
    prompts_file = swarm_root / "PROMPTS.md"
    if prompts_file.exists():
        return prompts_file.read_text()
    return "No prompts file found"


async def fetch_lane_knowledge(lane: str, rag_client) -> List[dict]:
    """Fetch lane-specific knowledge from RAG Brain.

    Args:
        lane: The lane to fetch knowledge for (KERNEL, ML, etc.)
        rag_client: RAGClient instance

    Returns:
        List of memory dicts with content, quality, etc.
    """
    query = f"{lane} best practices patterns"
    memories = await rag_client.recall(query, limit=5)
    return memories


async def fetch_all_lane_knowledge(rag_client) -> Dict[str, List[dict]]:
    """Fetch knowledge for all lanes from RAG Brain."""
    knowledge = {}
    for lane in LANE_PROMPTS.keys():
        memories = await fetch_lane_knowledge(lane, rag_client)
        knowledge[lane] = memories
    return knowledge


def fetch_lane_knowledge_sync(lane: str) -> List[dict]:
    """Synchronous wrapper to fetch lane knowledge."""
    from ..rag_client import get_rag_client
    rag_client = get_rag_client()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(fetch_lane_knowledge(lane, rag_client))
    except Exception:
        return []


def refresh_school_knowledge(state: SchoolState) -> SchoolState:
    """Refresh RAG knowledge for the selected lane."""
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
            return False, {}
        knowledge = await fetch_all_lane_knowledge(rag_client)
        return True, knowledge

    try:
        connected, knowledge = loop.run_until_complete(_fetch())
        state.rag_connected = connected
        state.lane_knowledge = knowledge
        state.last_knowledge_fetch = datetime.now()
    except Exception:
        state.rag_connected = False

    return state


def render_school(state: SchoolState) -> Panel:
    """Render school panel with curriculum, prompts, and pre-spawn knowledge."""
    content = Text()

    # Task types curriculum
    content.append(f"{BOOK_ICON} CURRICULUM\n", style="bold cyan")
    for task_type, desc in TASK_TYPES.items():
        content.append(f"  {task_type}: ", style="yellow")
        content.append(f"{desc}\n", style="dim")

    content.append(f"\n{GRAD_ICON} LANE PROMPTS\n", style="bold cyan")
    for lane, prompt in LANE_PROMPTS.items():
        marker = "\u25b6 " if lane == state.selected_lane else "  "
        style = "bold green" if lane == state.selected_lane else "green"
        content.append(f"{marker}[{lane}] ", style=style)
        content.append(f"{prompt}\n", style="white")

    # Pre-Spawn Knowledge section
    content.append(f"\n{BRAIN_ICON} PRE-SPAWN KNOWLEDGE", style="bold magenta")
    if state.rag_connected:
        content.append(" \U0001f7e2\n", style="green")
    else:
        content.append(" \U0001f534 (RAG offline)\n", style="red")

    lane_memories = state.lane_knowledge.get(state.selected_lane, [])
    if lane_memories:
        content.append(f"  Knowledge for [{state.selected_lane}]:\n", style="dim")
        for i, memory in enumerate(lane_memories[:5], 1):
            # Handle different memory formats
            if isinstance(memory, dict):
                mem_content = memory.get("content", memory.get("text", str(memory)))
                quality = memory.get("quality", 0.5)
            else:
                mem_content = str(memory)
                quality = 0.5

            # Truncate long content
            if len(mem_content) > 60:
                mem_content = mem_content[:57] + "..."

            # Quality indicator
            if quality >= 0.7:
                q_icon = "\U0001f7e2"
            elif quality >= 0.4:
                q_icon = "\U0001f7e1"
            else:
                q_icon = "\U0001f534"

            content.append(f"  {i}. {q_icon} ", style="dim")
            content.append(f"{mem_content}\n", style="white")

        content.append(f"\n  {INJECT_ICON} ", style="cyan")
        content.append(f"These will be injected into worker prompts\n", style="dim italic")
    else:
        content.append("  (No knowledge available for this lane)\n", style="dim italic")
        content.append("  Press [R] to refresh from RAG Brain\n", style="dim")

    # Footer with controls
    content.append("\n[1-5]", style="bold cyan")
    content.append("=Select Lane  ", style="dim")
    content.append("[R]", style="bold cyan")
    content.append("=Refresh  ", style="dim")
    content.append("[ESC]", style="bold yellow")
    content.append("=Close", style="dim")

    return Panel(
        content,
        title=f"{SCHOOL_ICON} SCHOOL - Training Center",
        border_style="yellow",
        width=75,
        height=28
    )
