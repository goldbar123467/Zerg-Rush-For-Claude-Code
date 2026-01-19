"""
Researcher Daemon - File Watcher and RAG Storage

Watches directories and stores changes to RAG Brain.
Background process that monitors file changes and queues them for research.

"All the news that's fit to embed."
"""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable

from ..rag_client import RAGClient


def hash_file(file_path: Path) -> str:
    """Compute MD5 hash of a file's contents."""
    try:
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest()
    except (IOError, OSError):
        return ""


def chunk_code(content: str, max_lines: int = 50) -> List[str]:
    """
    Chunk code into logical pieces by function/class boundaries.

    Args:
        content: Source code content
        max_lines: Maximum lines per chunk

    Returns:
        List of code chunks
    """
    lines = content.split('\n')
    chunks = []
    current_chunk = []

    for line in lines:
        # Start new chunk at function/class definitions if we're past 70% of max
        if (len(current_chunk) > max_lines * 0.7 and
            line.lstrip().startswith(('def ', 'class ', 'async def '))):
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            current_chunk = []

        current_chunk.append(line)

        # Force split at max_lines
        if len(current_chunk) >= max_lines:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []

    # Don't forget the last chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


class ResearcherDaemon:
    """
    Watches directories and stores changes to RAG Brain.

    Background process that polls for file changes and stores
    modified content to RAG for later recall.
    """

    def __init__(
        self,
        rag_client: RAGClient,
        message_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the researcher daemon.

        Args:
            rag_client: RAG Brain client for memory storage
            message_callback: Optional callback to report status messages
        """
        self.rag = rag_client
        self.message_callback = message_callback
        self.watch_paths: List[Path] = []
        self.file_hashes: Dict[Path, str] = {}  # Track file changes
        self.queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._watch_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
        self.poll_interval: float = 5.0  # Check every 5 seconds
        self.patterns: List[str] = ["*.py"]  # File patterns to watch
        self.files_processed: int = 0
        self.chunks_stored: int = 0
        self._error_count: int = 0
        self._max_backoff: float = 60.0

    def _log(self, message: str):
        """Log a message via callback or print."""
        if self.message_callback:
            self.message_callback(message)

    async def start(self):
        """Start the daemon watch and process loops."""
        if self.running:
            return

        self.running = True
        self._log("Researcher daemon started")

        # Start the background tasks
        self._watch_task = asyncio.create_task(self._watch_loop())
        self._process_task = asyncio.create_task(self._process_loop())

    async def stop(self):
        """Stop the daemon gracefully."""
        self.running = False

        # Cancel tasks
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None

        self._log("Researcher daemon stopped")

    def add_watch(self, path: Path, patterns: Optional[List[str]] = None):
        """
        Add a directory to the watch list.

        Args:
            path: Directory path to watch
            patterns: Optional list of glob patterns (default: ["*.py"])
        """
        if path.exists() and path.is_dir():
            self.watch_paths.append(path)
            if patterns:
                self.patterns = list(set(self.patterns + patterns))
            self._log(f"Added watch: {path}")

    def remove_watch(self, path: Path):
        """Remove a directory from the watch list."""
        if path in self.watch_paths:
            self.watch_paths.remove(path)
            self._log(f"Removed watch: {path}")

    async def _watch_loop(self):
        """Poll watched directories for file changes."""
        while self.running:
            try:
                for watch_path in self.watch_paths:
                    if not watch_path.exists():
                        continue

                    # Check each pattern
                    for pattern in self.patterns:
                        for file_path in watch_path.rglob(pattern):
                            if not file_path.is_file():
                                continue

                            # Skip large files (>100KB)
                            try:
                                if file_path.stat().st_size > 100 * 1024:
                                    continue
                            except OSError:
                                continue

                            current_hash = hash_file(file_path)
                            if not current_hash:
                                continue

                            # Check if file is new or changed
                            if file_path not in self.file_hashes:
                                # New file - initialize hash but don't queue
                                self.file_hashes[file_path] = current_hash
                            elif self.file_hashes[file_path] != current_hash:
                                # Changed file - queue for processing
                                self.file_hashes[file_path] = current_hash
                                await self.queue.put(file_path)
                                self._log(f"Queued: {file_path.name}")

                self._error_count = 0  # Reset on success
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._error_count += 1
                backoff = min(self.poll_interval * (2 ** self._error_count), self._max_backoff)
                self._log(f"Watch error (retry in {backoff:.0f}s): {e}")
                await asyncio.sleep(backoff)

    async def _process_loop(self):
        """Process queued file changes."""
        while self.running:
            try:
                # Wait for item with timeout
                file_path = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                await self._process_file(file_path)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Process error: {e}")

    async def _process_file(self, file_path: Path):
        """
        Read, chunk, and store a file to RAG Brain.

        Args:
            file_path: Path to the file to process
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (IOError, OSError) as e:
            self._log(f"Read error {file_path.name}: {e}")
            return

        # Chunk the content
        chunks = chunk_code(content, max_lines=50)

        tags = [
            file_path.name,
            file_path.parent.name,
            file_path.suffix.lstrip('.')
        ]

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            try:
                result = await self.rag.remember(
                    content=chunk,
                    category="code_snippet",
                    tags=tags + [f"chunk_{i}"],
                    source="researcher"
                )

                if result:
                    quality = result.get("predicted_quality",
                                        result.get("quality", 0))
                    self.chunks_stored += 1
                    self._log(
                        f"Stored {file_path.name}[{i}] | "
                        f"quality: {quality:.2f}"
                    )
            except Exception as e:
                self._log(f"Store error: {e}")

        self.files_processed += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get daemon statistics."""
        return {
            "running": self.running,
            "watch_paths": [str(p) for p in self.watch_paths],
            "patterns": self.patterns,
            "tracked_files": len(self.file_hashes),
            "queue_size": self.queue.qsize(),
            "files_processed": self.files_processed,
            "chunks_stored": self.chunks_stored,
            "poll_interval": self.poll_interval
        }


async def create_researcher_daemon(
    rag_client: RAGClient,
    watch_paths: Optional[List[Path]] = None,
    message_callback: Optional[Callable[[str], None]] = None
) -> ResearcherDaemon:
    """
    Factory function to create and configure a researcher daemon.

    Args:
        rag_client: RAG Brain client
        watch_paths: Initial paths to watch
        message_callback: Optional status message callback

    Returns:
        Configured ResearcherDaemon instance
    """
    daemon = ResearcherDaemon(rag_client, message_callback)

    if watch_paths:
        for path in watch_paths:
            daemon.add_watch(path)

    return daemon
