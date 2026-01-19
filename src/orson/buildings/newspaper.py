"""
Newspaper Office - The Researcher

Monitors file changes and manages research queue.
Stores findings to RAG Brain with quality feedback.
"All the news that's fit to embed."
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable, Any
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

NEWSPAPER_ICON = "📰"


@dataclass
class RAGFinding:
    """A finding stored in RAG Brain."""
    memory_id: str
    content_preview: str
    category: str
    quality: float
    stored_at: datetime = field(default_factory=datetime.now)

    @property
    def quality_icon(self) -> str:
        if self.quality >= 0.7:
            return "🟢"
        elif self.quality >= 0.4:
            return "🟡"
        return "🔴"

    @property
    def quality_label(self) -> str:
        if self.quality >= 0.7:
            return "Good memory"
        elif self.quality >= 0.4:
            return "Accepted"
        return "Rejected"

@dataclass
class WatchedPath:
    """A path being watched for changes."""
    path: str
    pattern: str  # e.g., "*.py", "**/*.md"
    last_checked: datetime = field(default_factory=datetime.now)
    last_modified: Optional[datetime] = None
    change_count: int = 0

@dataclass
class ResearchItem:
    """An item in the research queue."""
    path: str
    reason: str  # "new_file", "modified", "manual"
    queued_at: datetime = field(default_factory=datetime.now)
    processed: bool = False

@dataclass
class NewspaperState:
    """State for the newspaper office."""
    watch_list: List[WatchedPath] = field(default_factory=list)
    research_queue: List[ResearchItem] = field(default_factory=list)
    recent_findings: List[RAGFinding] = field(default_factory=list)
    is_visible: bool = False
    last_scan: Optional[datetime] = None
    input_mode: bool = False
    current_input: str = ""
    rag_callback: Optional[Callable] = None  # Async callback to RAG remember

def init_default_watches(project_root: Path) -> List[WatchedPath]:
    """Initialize default watch paths."""
    return [
        WatchedPath(path=str(project_root / "src"), pattern="**/*.py"),
        WatchedPath(path=str(project_root / "SWARM"), pattern="**/*.md"),
        WatchedPath(path=str(project_root / "tests"), pattern="**/*.py"),
    ]

def scan_for_changes(state: NewspaperState) -> List[str]:
    """Scan watched paths for changes since last check."""
    changes = []
    now = datetime.now()

    for watch in state.watch_list:
        path = Path(watch.path)
        if not path.exists():
            continue

        # Check modification times
        for file_path in path.glob(watch.pattern):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if watch.last_checked and mtime > watch.last_checked:
                    changes.append(str(file_path))
                    watch.change_count += 1

        watch.last_checked = now

    state.last_scan = now
    return changes

def queue_for_research(state: NewspaperState, path: str, reason: str = "manual"):
    """Add a file to the research queue."""
    item = ResearchItem(path=path, reason=reason)
    state.research_queue.append(item)

def render_newspaper(state: NewspaperState) -> Panel:
    """Render the newspaper office panel."""
    content = Text()

    # Input mode indicator
    if state.input_mode:
        content.append("📝 ADD RESEARCH (type, Enter to submit, Esc to cancel)\n", style="bold yellow")
        content.append(f"  > {state.current_input}_\n\n", style="white")

    # Recent findings with quality feedback
    if state.recent_findings:
        content.append("📚 RECENT FINDINGS\n", style="bold magenta")
        for finding in state.recent_findings[-5:]:
            content.append(f"  {finding.quality_icon} ", style="white")
            content.append(f"{finding.content_preview[:25]}... ", style="white")
            content.append(f"({finding.quality:.2f})\n", style="dim")
        content.append("\n")

    # Watch list (condensed)
    content.append("👁️ WATCHING\n", style="bold cyan")
    for watch in state.watch_list[:3]:
        path_short = Path(watch.path).name
        content.append(f"  📁 {path_short}/{watch.pattern} ", style="white")
        content.append(f"({watch.change_count})\n", style="yellow")

    # Research queue
    content.append("\n📋 QUEUE\n", style="bold green")
    pending = [r for r in state.research_queue if not r.processed]
    if pending:
        for item in pending[:3]:
            content.append(f"  • {Path(item.path).name} ", style="white")
            content.append(f"[{item.reason}]\n", style="dim")
        if len(pending) > 3:
            content.append(f"  +{len(pending)-3} more\n", style="dim")
    else:
        content.append("  (empty)\n", style="dim")

    # Instructions
    content.append("\n[a]=Add  [p]=Process  [Esc]=Close", style="dim")

    return Panel(
        content,
        title=f"{NEWSPAPER_ICON} NEWSPAPER OFFICE - Researcher",
        subtitle=f"Findings: {len(state.recent_findings)} | Queue: {len(pending)}",
        border_style="magenta"
    )

def get_recent_changes(state: NewspaperState, limit: int = 10) -> List[str]:
    """Get list of recently changed files."""
    recent = [r.path for r in state.research_queue if not r.processed]
    return recent[:limit]


async def store_to_rag(state: NewspaperState, content: str, category: str = "insight",
                       tags: Optional[List[str]] = None, rag_client: Any = None) -> Optional[RAGFinding]:
    """
    Store content to RAG Brain and track the finding.

    Args:
        state: NewspaperState to update
        content: Content to store
        category: Memory category (insight, code_snippet, etc.)
        tags: Optional tags
        rag_client: RAG client instance

    Returns:
        RAGFinding if successful, None otherwise
    """
    if rag_client is None:
        return None

    tags = tags or []
    result = await rag_client.remember(content, category=category, tags=tags)

    if result and isinstance(result, dict):
        finding = RAGFinding(
            memory_id=result.get("id", result.get("memory_id", "unknown")),
            content_preview=content[:50],
            category=category,
            quality=result.get("quality", 0.5)
        )
        state.recent_findings.append(finding)
        # Keep only last 20 findings
        if len(state.recent_findings) > 20:
            state.recent_findings = state.recent_findings[-20:]
        return finding
    return None


async def process_file_to_rag(state: NewspaperState, file_path: str,
                              rag_client: Any = None, chunk_fn: Any = None) -> List[RAGFinding]:
    """
    Read, chunk, and store a file to RAG Brain.

    Args:
        state: NewspaperState to update
        file_path: Path to file
        rag_client: RAG client instance
        chunk_fn: Function to chunk file content

    Returns:
        List of RAGFinding objects created
    """
    if rag_client is None:
        return []

    path = Path(file_path)
    if not path.exists():
        return []

    filename = path.name
    tags = [filename, path.suffix.lstrip('.')]

    # Chunk the file
    if chunk_fn:
        chunks = chunk_fn(path)
    else:
        try:
            chunks = [path.read_text()]
        except Exception:
            return []

    findings = []
    for i, chunk in enumerate(chunks):
        result = await rag_client.remember(
            chunk,
            category="code_snippet",
            tags=tags + [f"chunk_{i}"]
        )
        if result and isinstance(result, dict):
            finding = RAGFinding(
                memory_id=result.get("id", result.get("memory_id", "unknown")),
                content_preview=f"{filename}:{i}",
                category="code_snippet",
                quality=result.get("quality", 0.5)
            )
            findings.append(finding)
            state.recent_findings.append(finding)

    # Mark item as processed in queue
    for item in state.research_queue:
        if item.path == file_path:
            item.processed = True

    return findings


async def process_queue(state: NewspaperState, rag_client: Any = None,
                        chunk_fn: Any = None, max_items: int = 5) -> int:
    """
    Process pending items in the research queue.

    Returns:
        Number of items processed
    """
    pending = [r for r in state.research_queue if not r.processed][:max_items]
    processed = 0

    for item in pending:
        findings = await process_file_to_rag(state, item.path, rag_client, chunk_fn)
        if findings:
            processed += 1

    return processed
