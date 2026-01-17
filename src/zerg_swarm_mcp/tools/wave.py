"""Wave management MCP tools."""

from fastmcp import Context
from ..server import mcp
from ..config import settings
from .. import flavor
from .state import _load_state, _save_state

INBOX_DIR = settings.swarm_root / "INBOX"


@mcp.tool(name="wave_status", description="Get current wave info")
async def wave_status(ctx: Context) -> dict:
    """Return current wave number and statistics."""
    state = _load_state()

    # Check if swarm is idle
    voiceline = ""
    if len(state["active_zerglings"]) == 0 and len(state["pending_tasks"]) == 0:
        voiceline = flavor.idle()

    return {
        "wave": state["wave"],
        "active_zerglings": len(state["active_zerglings"]),
        "pending_tasks": len(state["pending_tasks"]),
        "completed_tasks": len(state["completed_tasks"]),
        "voiceline": voiceline
    }


@mcp.tool(name="wave_increment", description="Advance to next wave")
async def wave_increment(ctx: Context) -> dict:
    """Increment wave counter and return new wave number."""
    state = _load_state()
    old_wave = state["wave"]
    state["wave"] += 1
    _save_state(state)

    # Emit wave start voiceline
    voiceline = flavor.wave_start(state["wave"])

    return {"old_wave": old_wave, "new_wave": state["wave"], "voiceline": voiceline}


@mcp.tool(name="wave_collect", description="Collect results from INBOX")
async def wave_collect(ctx: Context) -> dict:
    """Process results from INBOX and update completed_tasks."""
    state = _load_state()
    collected = 0

    if INBOX_DIR.exists():
        for f in INBOX_DIR.glob("*_RESULT.md"):
            task_id = f.stem.replace("_RESULT", "")
            if task_id not in state["completed_tasks"]:
                state["completed_tasks"].append(task_id)
                collected += 1

    voiceline = ""
    if collected > 0:
        _save_state(state)
        # Emit wave/phase complete voiceline
        voiceline = flavor.wave_complete(state["wave"])

    return {
        "collected": collected,
        "total_completed": len(state["completed_tasks"]),
        "voiceline": voiceline
    }
