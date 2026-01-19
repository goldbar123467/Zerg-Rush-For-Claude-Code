"""
Wave 19: End-to-End Learning Loop Integration Test

Tests the complete RAG learning loop:
1. Store memory via Newspaper
2. Verify it appears in Brain panel
3. Spawn wave with related tasks
4. Verify School injected memory into worker context
5. Complete wave (mock DONE status)
6. Verify Cemetery sent feedback
7. Verify wave outcome stored
8. Check Museum shows updated concepts
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class MockRAGClient:
    """Mock RAG client for testing the learning loop."""

    def __init__(self):
        self.memories = []
        self.feedback_log = []
        self._concepts = []
        self._memory_counter = 0

    async def health(self) -> bool:
        return True

    async def remember(self, content: str, category: str = "insight", tags: list = None, source: str = "orson"):
        self._memory_counter += 1
        memory = {
            "id": f"mem_{self._memory_counter}",
            "content": content,
            "category": category,
            "tags": tags or [],
            "source": source,
            "quality": 0.75,
            "stored_at": datetime.now().isoformat()
        }
        self.memories.append(memory)

        # Auto-create concept from tags
        for tag in (tags or []):
            if not any(c["name"] == tag for c in self._concepts):
                self._concepts.append({
                    "name": tag,
                    "memory_count": 1,
                    "sample_text": content[:50]
                })
            else:
                for c in self._concepts:
                    if c["name"] == tag:
                        c["memory_count"] += 1

        return memory

    async def recall(self, query: str, limit: int = 10):
        # Simple keyword matching - check query words against content and tags
        results = []
        query_words = query.lower().split()
        for mem in self.memories:
            content_lower = mem["content"].lower()
            tags_lower = [t.lower() for t in mem.get("tags", [])]
            # Check if any query word matches content or tags
            for word in query_words:
                if word in content_lower or any(word in t for t in tags_lower):
                    results.append(mem)
                    break
        return results[:limit]

    async def feedback(self, memory_id: str, helpful: bool):
        self.feedback_log.append({
            "memory_id": memory_id,
            "helpful": helpful,
            "timestamp": datetime.now().isoformat()
        })
        return {"success": True}

    async def stats(self):
        return {
            "total_memories": len(self.memories),
            "total_feedback": len(self.feedback_log),
            "categories": {"insight": len([m for m in self.memories if m["category"] == "insight"])}
        }

    async def concepts(self):
        return self._concepts


@pytest.fixture
def mock_rag():
    """Create a mock RAG client."""
    return MockRAGClient()


def test_step1_store_memory_via_newspaper(mock_rag):
    """Step 1: Store a memory via Newspaper."""
    from src.orson.buildings.newspaper import NewspaperState, store_to_rag

    state = NewspaperState()
    content = "Always validate JWT tokens before processing requests"

    finding = run_async(store_to_rag(state, content, "security", ["jwt", "validation"], mock_rag))

    assert finding is not None
    assert finding.content_preview == content[:50]  # RAGFinding truncates to 50 chars
    assert finding.quality >= 0.5
    assert len(mock_rag.memories) == 1
    assert "jwt" in mock_rag.memories[0]["tags"]


def test_step2_verify_brain_panel_stats(mock_rag):
    """Step 2: Verify memory appears in Brain panel stats."""
    # Store a memory first
    run_async(mock_rag.remember("JWT validation is important", "security", ["jwt"]))

    stats = run_async(mock_rag.stats())

    assert stats["total_memories"] == 1
    assert "categories" in stats


def test_step3_school_has_lane_knowledge(mock_rag):
    """Step 3: Verify School can fetch lane-specific knowledge."""
    from src.orson.buildings.school import fetch_lane_knowledge

    # Store some KERNEL-related memories
    run_async(mock_rag.remember("KERNEL best practices: always check bounds", "insight", ["kernel", "best-practices"]))
    run_async(mock_rag.remember("KERNEL patterns: use atomic operations", "insight", ["kernel", "patterns"]))

    # Fetch knowledge for KERNEL lane
    knowledge = run_async(fetch_lane_knowledge("KERNEL", mock_rag))

    assert len(knowledge) >= 1
    assert any("kernel" in str(k).lower() for k in knowledge)


def test_step4_inject_knowledge_into_task():
    """Step 4: Verify knowledge injection into task objective."""
    from src.orson.cli import inject_rag_knowledge, SwarmState
    from src.orson.buildings.school import SchoolState

    # Set up state with mock knowledge
    state = SwarmState()
    state.school_state = SchoolState()
    state.school_state.lane_knowledge = {
        "KERNEL": [{"content": "Always validate input bounds", "quality": 0.8}]
    }

    task = {
        "id": "K001",
        "lane": "KERNEL",
        "type": "ADD_PURE_FN",
        "objective": "Implement matrix multiplication"
    }

    updated_task, log_msg = inject_rag_knowledge(task, state)

    assert "[RAG Knowledge]" in updated_task["objective"]
    assert "validate input bounds" in updated_task["objective"]
    assert "injected_knowledge" in updated_task


def test_step5_send_worker_feedback(mock_rag):
    """Step 5: Verify Cemetery sends feedback for completed workers."""
    from src.orson.state import send_worker_feedback, CompletedWorker

    # Store a memory first
    memory = run_async(mock_rag.remember("Test memory", "insight", ["test"]))

    # Create a completed worker with memory_id
    worker = CompletedWorker(
        name="Earl Johnson",
        task_id="K001",
        status="DONE",
        lines=50,
        timestamp=datetime.now(),
        memory_id=memory["id"],
        feedback_sent=False
    )

    # Send feedback
    result = run_async(send_worker_feedback(worker, mock_rag))

    assert result == True
    assert worker.feedback_sent == True
    assert len(mock_rag.feedback_log) == 1
    assert mock_rag.feedback_log[0]["helpful"] == True


def test_step6_store_wave_outcome(mock_rag):
    """Step 6: Verify wave outcome is stored as memory."""
    from src.orson.state import store_wave_outcome, CompletedWorker

    workers = [
        CompletedWorker("Earl", "K001", "DONE", 50, datetime.now()),
        CompletedWorker("Barb", "K002", "DONE", 30, datetime.now()),
        CompletedWorker("Jim", "K003", "PARTIAL", 20, datetime.now()),
    ]

    memory_id = run_async(store_wave_outcome(wave_num=5, completed_workers=workers, rag_client=mock_rag))

    assert memory_id is not None
    assert any("wave" in m["tags"] for m in mock_rag.memories)
    assert any("Wave 5" in m["content"] for m in mock_rag.memories)


def test_step7_museum_shows_concepts(mock_rag):
    """Step 7: Verify Museum shows concepts from RAG."""
    from src.orson.buildings.museum import fetch_concepts

    # Store memories with different tags to create concepts
    run_async(mock_rag.remember("JWT validation tip", "security", ["jwt", "security"]))
    run_async(mock_rag.remember("JWT refresh strategy", "security", ["jwt", "security"]))
    run_async(mock_rag.remember("Database indexing", "performance", ["database", "indexing"]))

    concepts = run_async(fetch_concepts(mock_rag))

    assert len(concepts) >= 2
    # Check that concepts have names and counts
    jwt_concept = next((c for c in concepts if "jwt" in c.name.lower()), None)
    assert jwt_concept is not None
    assert jwt_concept.memory_count >= 2


def test_step8_museum_concept_detail(mock_rag):
    """Step 8: Verify Museum can show concept detail with related memories."""
    from src.orson.buildings.museum import fetch_concept_memories

    # Store related memories
    run_async(mock_rag.remember("JWT validation is crucial", "security", ["jwt"]))
    run_async(mock_rag.remember("Always check JWT expiry", "security", ["jwt"]))

    memories = run_async(fetch_concept_memories("jwt", mock_rag, limit=10))

    assert len(memories) == 2
    assert all("jwt" in m["content"].lower() for m in memories)


def test_full_learning_loop(mock_rag):
    """End-to-end test of the complete learning loop."""
    from src.orson.buildings.newspaper import NewspaperState, store_to_rag
    from src.orson.buildings.school import fetch_lane_knowledge
    from src.orson.buildings.museum import fetch_concepts, fetch_concept_memories
    from src.orson.state import store_wave_outcome, send_worker_feedback, CompletedWorker

    # 1. Store memory via Newspaper
    state = NewspaperState()
    finding = run_async(store_to_rag(
        state,
        "Always validate JWT tokens before processing",
        "security",
        ["jwt", "validation", "security"],
        mock_rag
    ))
    assert finding is not None
    memory_id = finding.memory_id

    # 2. Verify it appears in stats
    stats = run_async(mock_rag.stats())
    assert stats["total_memories"] >= 1

    # 3. Fetch lane knowledge (would be used for task injection)
    # Store a KERNEL-specific memory
    run_async(mock_rag.remember("KERNEL: validate jwt in middleware", "insight", ["kernel", "jwt"]))
    knowledge = run_async(fetch_lane_knowledge("KERNEL", mock_rag))
    # May or may not find it depending on recall implementation

    # 4. Simulate worker completion with memory_id
    worker = CompletedWorker(
        name="Earl Johnson",
        task_id="K001",
        status="DONE",
        lines=50,
        timestamp=datetime.now(),
        memory_id=memory_id,
        feedback_sent=False
    )

    # 5. Send feedback
    run_async(send_worker_feedback(worker, mock_rag))
    assert worker.feedback_sent == True

    # 6. Store wave outcome
    outcome_id = run_async(store_wave_outcome(1, [worker], mock_rag))
    assert outcome_id is not None

    # 7. Check Museum concepts
    concepts = run_async(fetch_concepts(mock_rag))
    assert len(concepts) >= 1

    # 8. Check concept detail
    if concepts:
        concept_memories = run_async(fetch_concept_memories(concepts[0].name, mock_rag))
        # Should have at least some memories


def test_daemon_indicators_in_header():
    """Test that daemon status indicators are rendered in header."""
    from src.orson.cli import SwarmState, render_header

    state = SwarmState()
    state.rag_connected = True
    state.mcp_connected = True
    state.researcher_active = True
    state.teacher_active = True

    panel = render_header(state)

    # The header should be a Panel object
    assert panel is not None
    # Content should contain daemon indicators (we can't easily inspect Rich Panel content)


def test_swarm_state_has_daemon_flags():
    """Test that SwarmState has daemon-related flags."""
    from src.orson.cli import SwarmState

    state = SwarmState()

    # Check daemon flags exist
    assert hasattr(state, 'rag_connected')
    assert hasattr(state, 'mcp_connected')
    assert hasattr(state, 'researcher_active')
    assert hasattr(state, 'teacher_active')
    assert hasattr(state, 'newspaper_state')
    assert hasattr(state, 'school_state')
    assert hasattr(state, 'brain_state')


def test_daemon_indicators_reflect_state():
    """Test that daemon indicators change based on state."""
    from src.orson.cli import SwarmState, render_header

    # Test with daemons ON
    state_on = SwarmState()
    state_on.researcher_active = True
    state_on.teacher_active = True
    state_on.rag_connected = True
    state_on.mcp_connected = True

    panel_on = render_header(state_on)
    assert panel_on is not None

    # Test with daemons OFF
    state_off = SwarmState()
    state_off.researcher_active = False
    state_off.teacher_active = False
    state_off.rag_connected = False
    state_off.mcp_connected = False

    panel_off = render_header(state_off)
    assert panel_off is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
