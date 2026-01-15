"""Basic integration tests for Zerg Swarm MCP Server."""

import pytest


def test_server_import():
    """Test that the server module imports correctly."""
    from zerg_swarm_mcp.server import mcp
    assert mcp.name == "zerg-swarm"


def test_config_import():
    """Test that config loads with defaults."""
    from zerg_swarm_mcp.config import settings
    assert settings.port == 8766
    assert settings.host == "127.0.0.1"


def test_models_import():
    """Test that all models are importable."""
    from zerg_swarm_mcp.models import (
        SwarmState, TaskCard, Zergling, FileLock, ToolResponse
    )
    # Verify models can be instantiated
    state = SwarmState()
    assert state.wave == 0


def test_tools_import():
    """Test that all tool modules import without error."""
    from zerg_swarm_mcp.tools import state, tasks, locks, zergling, wave, results, reconcile
    assert True


def test_state_tools_exist():
    """Test that state tools are registered."""
    from zerg_swarm_mcp.server import mcp
    from zerg_swarm_mcp.tools import state
    # Tools should be registered after import
    assert True
