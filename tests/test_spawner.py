"""
Tests for the Orson Spawner module.

Tests tmux session management, worker spawning, and monitoring.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_spawner_imports():
    """Test spawner module imports."""
    from src.orson.spawner import (
        SpawnerState, SpawnedWorker, check_tmux_available, check_claude_available,
        get_spawner_state, spawn_wave, collect_completed, kill_all_workers,
        generate_task_prompt
    )
    assert SpawnerState is not None
    assert SpawnedWorker is not None


def test_spawned_worker_dataclass():
    """Test SpawnedWorker dataclass properties."""
    from src.orson.spawner import SpawnedWorker

    worker = SpawnedWorker(
        name="Earl",
        session_name="worker-earl-k001",
        task_id="K001",
        lane="KERNEL",
        task_type="ADD_PURE_FN",
        objective="Test objective",
        spawned_at=datetime.now()
    )

    assert worker.name == "Earl"
    assert worker.task_id == "K001"
    assert worker.status == "running"
    assert worker.progress >= 0
    assert worker.progress <= 1
    assert not worker.is_expired


def test_worker_ttl_progress():
    """Test worker TTL progress calculation."""
    from src.orson.spawner import SpawnedWorker

    # Worker spawned 2 minutes ago (halfway through 4-min TTL)
    worker = SpawnedWorker(
        name="Barb",
        session_name="worker-barb-k002",
        task_id="K002",
        lane="KERNEL",
        task_type="ADD_TEST",
        objective="Test TTL",
        spawned_at=datetime.now() - timedelta(minutes=2)
    )

    # Progress should be around 50%
    assert 0.4 <= worker.progress <= 0.6
    assert not worker.is_expired
    assert worker.time_remaining.total_seconds() > 0


def test_worker_expired():
    """Test worker expiration detection."""
    from src.orson.spawner import SpawnedWorker

    # Worker spawned 5 minutes ago (past 4-min TTL)
    worker = SpawnedWorker(
        name="Jim",
        session_name="worker-jim-k003",
        task_id="K003",
        lane="KERNEL",
        task_type="FIX_ONE_BUG",
        objective="Test expiration",
        spawned_at=datetime.now() - timedelta(minutes=5)
    )

    assert worker.is_expired
    assert worker.progress >= 1.0
    assert worker.time_remaining.total_seconds() == 0


def test_spawner_state_initialization():
    """Test SpawnerState initialization."""
    from src.orson.spawner import SpawnerState

    state = SpawnerState()
    assert state.active_workers == []
    assert state.completed_workers == []
    assert state.wave == 0
    assert state.tmux_available == True


def test_check_tmux_available():
    """Test tmux availability check."""
    from src.orson.spawner import check_tmux_available

    # This will return True if tmux is installed
    result = check_tmux_available()
    assert isinstance(result, bool)


def test_check_claude_available():
    """Test Claude CLI availability check."""
    from src.orson.spawner import check_claude_available

    # This will return True if claude is in PATH
    result = check_claude_available()
    assert isinstance(result, bool)


def test_generate_task_prompt():
    """Test task prompt generation."""
    from src.orson.spawner import generate_task_prompt

    task = {
        "id": "K001",
        "lane": "KERNEL",
        "type": "ADD_PURE_FN",
        "objective": "Implement matrix multiplication",
        "injected_knowledge": "Use atomic operations for thread safety"
    }
    swarm_root = Path("/tmp/test-swarm")

    prompt = generate_task_prompt(task, swarm_root)

    assert "K001" in prompt
    assert "KERNEL" in prompt
    assert "ADD_PURE_FN" in prompt
    assert "matrix multiplication" in prompt
    assert "atomic operations" in prompt
    assert "4 minutes" in prompt
    assert "100 new lines" in prompt
    assert "INBOX" in prompt


def test_generate_task_prompt_no_knowledge():
    """Test task prompt generation without RAG knowledge."""
    from src.orson.spawner import generate_task_prompt

    task = {
        "id": "M001",
        "lane": "ML",
        "type": "ADD_TEST",
        "objective": "Add tests for model loader"
    }
    swarm_root = Path("/tmp/test-swarm")

    prompt = generate_task_prompt(task, swarm_root)

    assert "M001" in prompt
    assert "ML" in prompt
    assert "model loader" in prompt
    assert "RAG" not in prompt  # No knowledge section


def test_get_spawner_state_singleton():
    """Test spawner state singleton."""
    from src.orson.spawner import get_spawner_state, reset_spawner_state

    # Reset first
    reset_spawner_state()

    state1 = get_spawner_state()
    state2 = get_spawner_state()

    # Should return same instance
    assert state1 is state2


def test_collect_completed_no_workers():
    """Test collect_completed with no active workers."""
    from src.orson.spawner import SpawnerState, collect_completed

    state = SpawnerState()
    result = collect_completed(state)

    assert result.active_workers == []
    assert result.completed_workers == []


def test_kill_all_workers_no_workers():
    """Test kill_all_workers with no active workers."""
    from src.orson.spawner import SpawnerState, kill_all_workers

    state = SpawnerState()
    result = kill_all_workers(state)

    assert result.active_workers == []
    assert result.completed_workers == []


def test_cli_has_spawner_state():
    """Test that CLI SwarmState has spawner state."""
    from src.orson.cli import SwarmState

    state = SwarmState()

    assert hasattr(state, 'spawner_state')
    assert hasattr(state, 'real_spawn_enabled')
    assert hasattr(state, 'tmux_available')
    assert hasattr(state, 'claude_available')


def test_render_zerglings_with_workers():
    """Test render_zerglings shows real workers."""
    from src.orson.cli import SwarmState, render_zerglings
    from src.orson.spawner import SpawnedWorker

    state = SwarmState()
    state.spawner_state.active_workers = [
        SpawnedWorker(
            name="Earl",
            session_name="worker-earl-k001",
            task_id="K001",
            lane="KERNEL",
            task_type="ADD_PURE_FN",
            objective="Test",
            spawned_at=datetime.now()
        )
    ]

    panel = render_zerglings(state)
    assert panel is not None


def test_render_buildings_with_active_workers():
    """Test render_buildings shows active workers per lane."""
    from src.orson.cli import SwarmState, render_buildings
    from src.orson.spawner import SpawnedWorker

    state = SwarmState()
    # Add workers to different lanes
    state.spawner_state.active_workers = [
        SpawnedWorker(
            name="Earl",
            session_name="worker-earl-k001",
            task_id="K001",
            lane="KERNEL",
            task_type="ADD_PURE_FN",
            objective="Test KERNEL task",
            spawned_at=datetime.now()
        ),
        SpawnedWorker(
            name="Barb",
            session_name="worker-barb-m001",
            task_id="M001",
            lane="ML",
            task_type="ADD_TEST",
            objective="Test ML task",
            spawned_at=datetime.now() - timedelta(minutes=1)
        ),
        SpawnedWorker(
            name="Jim",
            session_name="worker-jim-k002",
            task_id="K002",
            lane="KERNEL",
            task_type="FIX_ONE_BUG",
            objective="Fix KERNEL bug",
            spawned_at=datetime.now() - timedelta(minutes=2)
        ),
    ]

    panel = render_buildings(state)
    assert panel is not None
    # Panel should be created successfully with worker display


def test_render_buildings_no_workers():
    """Test render_buildings works without active workers."""
    from src.orson.cli import SwarmState, render_buildings

    state = SwarmState()
    state.spawner_state.active_workers = []

    panel = render_buildings(state)
    assert panel is not None


def test_parse_worker_result_done():
    """Test parsing DONE status from output."""
    from src.orson.spawner import parse_worker_result

    output = """
    Working on task K001...
    DONE: K001 - added jwt_validate function
    | Lines | 42 |
    """
    status, task_id, message, lines = parse_worker_result(output)

    assert status == "DONE"
    assert task_id == "K001"
    assert "jwt_validate" in message
    assert lines == 42


def test_parse_worker_result_partial():
    """Test parsing PARTIAL status from output."""
    from src.orson.spawner import parse_worker_result

    output = """
    Working on task M001...
    PARTIAL: M001 - implemented loader but tests incomplete
    Lines: 75
    """
    status, task_id, message, lines = parse_worker_result(output)

    assert status == "PARTIAL"
    assert task_id == "M001"
    assert "loader" in message
    assert lines == 75


def test_parse_worker_result_blocked():
    """Test parsing BLOCKED status from output."""
    from src.orson.spawner import parse_worker_result

    output = """
    BLOCKED: Q001 - missing API credentials
    """
    status, task_id, message, lines = parse_worker_result(output)

    assert status == "BLOCKED"
    assert task_id == "Q001"
    assert "credentials" in message


def test_parse_worker_result_table_format():
    """Test parsing status from table format."""
    from src.orson.spawner import parse_worker_result

    output = """
    | Status | DONE |
    | Lines | 30 |
    """
    status, task_id, message, lines = parse_worker_result(output)

    assert status == "DONE"
    assert lines == 30


def test_parse_worker_result_colon_format():
    """Test parsing status from colon format."""
    from src.orson.spawner import parse_worker_result

    output = """
    Status: PARTIAL
    Lines: 55
    """
    status, task_id, message, lines = parse_worker_result(output)

    assert status == "PARTIAL"
    assert lines == 55


def test_parse_worker_result_unknown():
    """Test parsing unknown status from output."""
    from src.orson.spawner import parse_worker_result

    output = "Some random output with no status"
    status, task_id, message, lines = parse_worker_result(output)

    assert status == "UNKNOWN"
    assert lines == 0


def test_handle_worker_death():
    """Test handle_worker_death updates state correctly."""
    from src.orson.cli import SwarmState, handle_worker_death
    from src.orson.spawner import SpawnedWorker

    state = SwarmState()
    state.tasks_by_lane = {
        "KERNEL": [{"id": "K001", "type": "ADD_PURE_FN", "status": "IN_PROGRESS"}]
    }

    worker = SpawnedWorker(
        name="Earl",
        session_name="worker-earl-k001",
        task_id="K001",
        lane="KERNEL",
        task_type="ADD_PURE_FN",
        objective="Test task",
        spawned_at=datetime.now()
    )

    state = handle_worker_death(state, worker, "DONE", "completed successfully", 50)

    # Check worker added to completed lists
    assert len(state.spawner_state.completed_workers) == 1
    assert len(state.completed_workers) == 1

    # Check task status updated
    assert state.tasks_by_lane["KERNEL"][0]["status"] == "DONE"

    # Check radio events added (status, church, cemetery = 3 events)
    assert len(state.radio_events) == 3
    # Check status event
    assert "Earl" in state.radio_events[0]["message"]
    assert "K001" in state.radio_events[0]["message"]
    # Check church animation
    assert "church" in state.radio_events[1]["message"].lower()
    # Check cemetery event with epitaph
    assert "Earl" in state.radio_events[2]["message"]

    # Check tombstone added to cemetery
    assert len(state.cemetery) == 1
    tombstone = state.cemetery[0]
    assert tombstone.worker_name == "Earl"
    assert tombstone.task_id == "K001"
    assert tombstone.status == "DONE"
    assert tombstone.lines_written == 50
    assert tombstone.epitaph is not None
    assert len(tombstone.epitaph) > 0

    # Check worker returned to pool
    assert any(w.name == "Earl" for w in state.apartments_state.idle_workers)


def test_handle_worker_death_timeout():
    """Test handle_worker_death for timeout status."""
    from src.orson.cli import SwarmState, handle_worker_death
    from src.orson.spawner import SpawnedWorker

    state = SwarmState()
    worker = SpawnedWorker(
        name="Jim",
        session_name="worker-jim-k002",
        task_id="K002",
        lane="KERNEL",
        task_type="FIX_ONE_BUG",
        objective="Test timeout",
        spawned_at=datetime.now()
    )

    state = handle_worker_death(state, worker, "TIMEOUT", "exceeded TTL", 0)

    # Check tombstone has TIMEOUT status
    assert len(state.cemetery) == 1
    assert state.cemetery[0].status == "TIMEOUT"

    # Worker should NOT be returned to pool on timeout
    assert not any(w.name == "Jim" for w in state.apartments_state.idle_workers)


def test_monitor_workers_sync_no_workers():
    """Test monitor_workers_sync with no active workers."""
    from src.orson.cli import SwarmState, monitor_workers_sync

    state = SwarmState()
    state.spawner_state.active_workers = []

    updated_state = monitor_workers_sync(state)

    assert updated_state.spawner_state.active_workers == []


def test_cleanup_worker_session():
    """Test cleanup_worker_session function."""
    from src.orson.spawner import cleanup_worker_session, SpawnedWorker

    worker = SpawnedWorker(
        name="Test",
        session_name="nonexistent-session",
        task_id="T001",
        lane="KERNEL",
        task_type="TEST",
        objective="Test",
        spawned_at=datetime.now()
    )

    # Should not fail even if session doesn't exist
    result = cleanup_worker_session(worker)
    assert result == True


def test_get_epitaph():
    """Test get_epitaph returns epitaphs for each status."""
    from src.orson.state import get_epitaph, EPITAPHS

    # Test all known statuses
    for status in ["DONE", "PARTIAL", "BLOCKED", "TIMEOUT", "FAILED"]:
        epitaph = get_epitaph(status)
        assert epitaph is not None
        assert len(epitaph) > 0
        assert epitaph in EPITAPHS[status]

    # Test unknown status falls back to UNKNOWN
    unknown_epitaph = get_epitaph("WEIRD_STATUS")
    assert unknown_epitaph in EPITAPHS["UNKNOWN"]


def test_count_lines_in_output():
    """Test count_lines_in_output parses various formats."""
    from src.orson.state import count_lines_in_output

    # Table format
    assert count_lines_in_output("| Lines | 42 |") == 42

    # Colon format
    assert count_lines_in_output("Lines: 75") == 75

    # Natural language
    assert count_lines_in_output("Added 30 lines to the file") == 30
    assert count_lines_in_output("50 lines written") == 50

    # No lines found
    assert count_lines_in_output("No line info here") == 0


def test_tombstone_dataclass():
    """Test Tombstone dataclass."""
    from src.orson.state import Tombstone

    tombstone = Tombstone(
        worker_name="Earl",
        task_id="K001",
        status="DONE",
        wave=5,
        lines_written=42,
        epitaph="Did the job right"
    )

    assert tombstone.worker_name == "Earl"
    assert tombstone.task_id == "K001"
    assert tombstone.status == "DONE"
    assert tombstone.wave == 5
    assert tombstone.lines_written == 42
    assert tombstone.epitaph == "Did the job right"
    assert tombstone.timestamp is not None


def test_swarm_state_has_cemetery():
    """Test SwarmState has cemetery field."""
    from src.orson.cli import SwarmState

    state = SwarmState()
    assert hasattr(state, 'cemetery')
    assert state.cemetery == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
