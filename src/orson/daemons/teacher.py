"""
Teacher Daemon - Knowledge Injector for Workers

Periodically queries RAG Brain and updates lane-specific prompts.
Synthesizes lessons from past experiences to improve worker performance.

"Those who cannot remember the past are condemned to repeat it."
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable

from ..rag_client import RAGClient


class TeacherDaemon:
    """
    Periodically queries RAG and updates lane prompts.

    Background process that synthesizes knowledge from RAG Brain
    into actionable lessons for workers in each lane.
    """

    LANES = ["KERNEL", "ML", "QUANT", "DEX", "INTEGRATION"]

    def __init__(
        self,
        rag_client: RAGClient,
        prompts_dir: Optional[Path] = None,
        message_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the teacher daemon.

        Args:
            rag_client: RAG Brain client for memory queries
            prompts_dir: Directory for lane prompt files
            message_callback: Optional callback to report status messages
        """
        self.rag = rag_client
        self.message_callback = message_callback
        self.running = False
        self.lesson_interval: float = 300.0  # 5 minutes
        self.prompts_dir = prompts_dir or Path("SWARM/PROMPTS")
        self._teach_task: Optional[asyncio.Task] = None
        self.prompt_versions: Dict[str, int] = {}
        self.lessons_taught: int = 0
        self.last_teach_time: Optional[datetime] = None

    def _log(self, message: str):
        """Log a message via callback."""
        if self.message_callback:
            self.message_callback(message)

    async def start(self):
        """Start the teaching loop."""
        if self.running:
            return

        self.running = True
        self._log("Teacher daemon started")

        # Ensure prompts directory exists
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Start the background task
        self._teach_task = asyncio.create_task(self._teach_loop())

    async def stop(self):
        """Stop the daemon gracefully."""
        self.running = False

        if self._teach_task:
            self._teach_task.cancel()
            try:
                await self._teach_task
            except asyncio.CancelledError:
                pass
            self._teach_task = None

        self._log("Teacher daemon stopped")

    async def _teach_loop(self):
        """Periodically synthesize lessons and update prompts."""
        while self.running:
            try:
                await self._teach_all_lanes()
                await asyncio.sleep(self.lesson_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Teach error: {e}")
                await asyncio.sleep(60)  # Wait a minute on error

    async def _teach_all_lanes(self):
        """Query RAG and update each lane's prompts."""
        self.last_teach_time = datetime.now()
        errors = []

        for lane in self.LANES:
            success = False
            for attempt in range(3):  # 3 retries per lane
                try:
                    await self._teach_lane(lane)
                    success = True
                    break
                except Exception as e:
                    if attempt == 2:  # Final attempt
                        errors.append(f"{lane}: {str(e)[:30]}")
                        self._log(f"Failed teaching {lane} after 3 attempts: {e}")
                    else:
                        await asyncio.sleep(1)  # Brief delay before retry

            if success:
                self._log(f"Taught {lane}")

        if errors:
            self._log(f"Teaching cycle complete with {len(errors)} errors")
        else:
            self._log("Teaching cycle complete - all lanes updated")

    async def _teach_lane(self, lane: str):
        """
        Query RAG for lane-specific knowledge and update prompts.

        Args:
            lane: Lane name (KERNEL, ML, etc.)
        """
        # Query for lane-specific knowledge
        query = f"{lane} best practices patterns lessons"
        memories = await self.rag.recall(query, limit=10)

        if not memories:
            return

        # Synthesize into lesson
        lesson = self._synthesize_lesson(lane, memories)

        if not lesson:
            return

        # Update prompt file
        await self._update_lane_prompt(lane, lesson)

        # Track version
        self.prompt_versions[lane] = self.prompt_versions.get(lane, 0) + 1
        self.lessons_taught += 1

        preview = lesson[:50].replace('\n', ' ')
        self._log(f"Taught {lane}: {preview}...")

    def _synthesize_lesson(self, lane: str, memories: List[Dict]) -> str:
        """
        Combine memories into a coherent lesson.

        Args:
            lane: Lane name
            memories: List of memory dicts from RAG recall

        Returns:
            Synthesized lesson text
        """
        if not memories:
            return ""

        points = []
        for mem in memories[:5]:  # Top 5 by relevance
            content = mem.get("content", "")
            if not content:
                continue

            # Truncate long content
            if len(content) > 150:
                content = content[:150] + "..."

            # Clean up for display
            content = content.replace('\n', ' ').strip()
            if content:
                points.append(f"- {content}")

        if not points:
            return ""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return (
            f"Updated: {timestamp}\n"
            f"Recent learnings for {lane}:\n" +
            "\n".join(points)
        )

    async def _update_lane_prompt(self, lane: str, lesson: str):
        """
        Append lesson to lane prompt file.

        Args:
            lane: Lane name
            lesson: Lesson content to add
        """
        prompt_file = self.prompts_dir / f"{lane}.prompt"

        # Read existing content
        if prompt_file.exists():
            try:
                existing = prompt_file.read_text(encoding="utf-8", errors="replace")
            except IOError:
                existing = ""
        else:
            existing = f"# {lane} Worker Prompt\n\nContext and guidance for {lane} workers.\n"

        # Marker for learnings section
        marker = "## RECENT LEARNINGS"

        if marker in existing:
            # Replace existing learnings section
            before = existing.split(marker)[0].rstrip()
            updated = f"{before}\n\n{marker}\n{lesson}\n"
        else:
            # Append new section
            updated = f"{existing.rstrip()}\n\n{marker}\n{lesson}\n"

        # Write atomically
        temp_file = prompt_file.with_suffix(".tmp")
        try:
            temp_file.write_text(updated, encoding="utf-8")
            temp_file.rename(prompt_file)
        except IOError as e:
            self._log(f"Write error {lane}: {e}")

    async def teach_now(self):
        """Force immediate teaching of all lanes."""
        self._log("Force teaching all lanes...")
        await self._teach_all_lanes()
        self._log("Force teach complete")

    async def teach_lane(self, lane: str):
        """
        Force immediate teaching of a specific lane.

        Args:
            lane: Lane name to teach
        """
        if lane not in self.LANES:
            self._log(f"Unknown lane: {lane}")
            return

        self._log(f"Force teaching {lane}...")
        await self._teach_lane(lane)

    def get_stats(self) -> Dict[str, Any]:
        """Get daemon statistics."""
        return {
            "running": self.running,
            "lessons_taught": self.lessons_taught,
            "prompt_versions": dict(self.prompt_versions),
            "last_teach_time": self.last_teach_time.isoformat() if self.last_teach_time else None,
            "lesson_interval": self.lesson_interval,
            "prompts_dir": str(self.prompts_dir)
        }

    def get_lane_prompt(self, lane: str) -> Optional[str]:
        """
        Read the current prompt for a lane.

        Args:
            lane: Lane name

        Returns:
            Prompt content or None if not found
        """
        prompt_file = self.prompts_dir / f"{lane}.prompt"
        if prompt_file.exists():
            try:
                return prompt_file.read_text(encoding="utf-8", errors="replace")
            except IOError:
                pass
        return None


async def create_teacher_daemon(
    rag_client: RAGClient,
    prompts_dir: Optional[Path] = None,
    message_callback: Optional[Callable[[str], None]] = None
) -> TeacherDaemon:
    """
    Factory function to create a teacher daemon.

    Args:
        rag_client: RAG Brain client
        prompts_dir: Directory for prompt files
        message_callback: Optional status message callback

    Returns:
        Configured TeacherDaemon instance
    """
    return TeacherDaemon(rag_client, prompts_dir, message_callback)
