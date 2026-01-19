"""
RAG Brain Async REST Client for Orson CLI

Connects to RAG Brain server at http://localhost:8000.
Provides async methods for memory operations.
"""

import asyncio
import aiohttp
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, List


@dataclass
class RAGMemory:
    """A memory stored in RAG Brain with quality tracking."""
    memory_id: str
    content: str
    category: str
    quality: float
    tags: List[str] = field(default_factory=list)
    stored_at: datetime = field(default_factory=datetime.now)

    @property
    def quality_icon(self) -> str:
        """Get quality indicator icon."""
        if self.quality >= 0.7:
            return "🟢"
        elif self.quality >= 0.4:
            return "🟡"
        else:
            return "🔴"

    @property
    def quality_label(self) -> str:
        """Get quality label."""
        if self.quality >= 0.7:
            return "Good memory"
        elif self.quality >= 0.4:
            return "Accepted"
        else:
            return "Rejected by Gatekeeper"


def format_quality_display(quality: float) -> str:
    """Format quality score for display."""
    if quality >= 0.7:
        return f"🟢 {quality:.2f} Good memory"
    elif quality >= 0.4:
        return f"🟡 {quality:.2f} Accepted"
    else:
        return f"🔴 {quality:.2f} Rejected by Gatekeeper"


def chunk_file(file_path: Path, max_chunk_size: int = 500) -> List[str]:
    """Read and chunk a file for RAG storage."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    if file_path.suffix in ['.py', '.js', '.ts']:
        return _chunk_code(content, max_chunk_size)
    return _chunk_text(content, max_chunk_size)


def _chunk_code(content: str, max_size: int) -> List[str]:
    """Chunk code by logical boundaries."""
    chunks, current, size = [], [], 0
    for line in content.split('\n'):
        if size > max_size * 0.7 and line.startswith(('def ', 'class ', 'async def ')):
            if current:
                chunks.append('\n'.join(current))
            current, size = [], 0
        current.append(line)
        size += len(line) + 1
        if size >= max_size:
            chunks.append('\n'.join(current))
            current, size = [], 0
    if current:
        chunks.append('\n'.join(current))
    return chunks


def _chunk_text(content: str, max_size: int) -> List[str]:
    """Chunk text by paragraph boundaries."""
    chunks, current, size = [], [], 0
    for para in content.split('\n\n'):
        if size + len(para) > max_size and current:
            chunks.append('\n\n'.join(current))
            current, size = [], 0
        current.append(para)
        size += len(para) + 2
    if current:
        chunks.append('\n\n'.join(current))
    return chunks


class RAGClient:
    """Async REST client for RAG Brain API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_error: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.close()
        return False

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _get(self, path: str) -> Optional[Any]:
        """Make a GET request."""
        self.last_error = None
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}{path}", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
                self.last_error = f"HTTP {resp.status}"
        except aiohttp.ClientError as e:
            self.last_error = f"Connection: {str(e)[:40]}"
        except asyncio.TimeoutError:
            self.last_error = "Request timeout"
        except Exception as e:
            self.last_error = f"Error: {str(e)[:40]}"
        return None

    async def _post(self, path: str, data: dict) -> Optional[Any]:
        """Make a POST request."""
        self.last_error = None
        try:
            await self._ensure_session()
            async with self.session.post(f"{self.base_url}{path}", json=data, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
                self.last_error = f"HTTP {resp.status}"
        except aiohttp.ClientError as e:
            self.last_error = f"Connection: {str(e)[:40]}"
        except asyncio.TimeoutError:
            self.last_error = "Request timeout"
        except Exception as e:
            self.last_error = f"Error: {str(e)[:40]}"
        return None

    def get_last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self.last_error

    async def health(self) -> bool:
        """Check if RAG Brain server is healthy."""
        result = await self._get("/health")
        return result is not None

    async def remember(self, content: str, category: str = "insight", tags: list = None, source: str = "orson") -> Optional[dict]:
        """Store a memory in RAG Brain."""
        return await self._post("/remember", {
            "content": content,
            "category": category,
            "tags": tags or [],
            "source": source
        })

    async def recall(self, query: str, limit: int = 10) -> list:
        """Recall memories matching a query."""
        result = await self._post("/recall", {"query": query, "limit": limit})
        return result if isinstance(result, list) else []

    async def feedback(self, memory_id: str, helpful: bool) -> Optional[dict]:
        """Provide feedback on a memory."""
        return await self._post("/feedback", {"memory_id": memory_id, "helpful": helpful})

    async def stats(self) -> Optional[dict]:
        """Get RAG Brain statistics."""
        return await self._get("/stats")

    async def concepts(self) -> list:
        """Get list of concepts from RAG Brain."""
        result = await self._get("/concepts")
        return result if isinstance(result, list) else []


# Singleton instance
_client: Optional[RAGClient] = None


def get_rag_client() -> RAGClient:
    """Get or create the singleton RAG client."""
    global _client
    if _client is None:
        _client = RAGClient()
    return _client
