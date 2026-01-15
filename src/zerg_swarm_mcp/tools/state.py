"""State management MCP tools."""

import json
from datetime import datetime
from pathlib import Path
from fastmcp import Context
from ..server import mcp
from ..config import settings

STATE_FILE = settings.swarm_root / "STATE.json"


def _load_state() -> dict:
    """Load state from file with defaults."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "wave": 0,
            "active_zerglings": [],
            "completed_tasks": [],
            "pending_tasks": [],
            "last_updated": ""
        }


def _save_state(state: dict) -> None:
    """Save state atomically."""
    state["last_updated"] = datetime.now().isoformat()
    temp = STATE_FILE.with_suffix(".tmp")
    with open(temp, "w") as f:
        json.dump(state, f, indent=2)
    temp.replace(STATE_FILE)


@mcp.tool(name="swarm_status", description="Get current swarm state")
async def swarm_status(ctx: Context) -> dict:
    """Return current swarm state including wave, zerglings, and tasks."""
    return _load_state()


@mcp.tool(name="swarm_reset", description="Reset swarm to initial state")
async def swarm_reset(ctx: Context) -> dict:
    """Reset all swarm state to initial values."""
    state = {
        "wave": 0,
        "active_zerglings": [],
        "completed_tasks": [],
        "pending_tasks": [],
        "last_updated": ""
    }
    _save_state(state)
    return {"status": "reset", "state": state}
