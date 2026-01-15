"""Reconciliation and diagnostics MCP tools."""

from pathlib import Path
from fastmcp import Context
from ..server import mcp
from ..config import settings
from .state import _load_state, _save_state

TASKS_DIR = settings.swarm_root / "TASKS"
LANES = ["KERNEL", "ML", "QUANT", "DEX", "INTEGRATION"]


@mcp.tool(name="reconcile_state", description="Sync state with task files")
async def reconcile_state(ctx: Context, fix: bool = False) -> dict:
    """Compare STATE.json pending_tasks with actual task files."""
    state = _load_state()
    
    # Scan for actual tasks
    actual_tasks = set()
    for lane in LANES:
        lane_dir = TASKS_DIR / lane
        if lane_dir.exists():
            for f in lane_dir.glob("*.md"):
                if f.name != "README.md":
                    actual_tasks.add(f"{lane}/{f.stem}")
    
    pending = set(state["pending_tasks"])
    
    missing_in_state = actual_tasks - pending
    orphaned_in_state = pending - actual_tasks
    
    result = {
        "missing_in_state": list(missing_in_state),
        "orphaned_in_state": list(orphaned_in_state),
        "in_sync": len(missing_in_state) == 0 and len(orphaned_in_state) == 0
    }
    
    if fix and not result["in_sync"]:
        state["pending_tasks"] = sorted(actual_tasks)
        _save_state(state)
        result["fixed"] = True
    
    return result


@mcp.tool(name="health_check", description="System diagnostics")
async def health_check(ctx: Context) -> dict:
    """Return swarm system health status."""
    state = _load_state()
    
    # Check directories
    dirs_exist = {
        "TASKS": (settings.swarm_root / "TASKS").exists(),
        "INBOX": (settings.swarm_root / "INBOX").exists(),
        "OUTBOX": (settings.swarm_root / "OUTBOX").exists(),
        "LOCKS": (settings.swarm_root / "LOCKS").exists(),
        "ARCHIVE": (settings.swarm_root / "ARCHIVE").exists(),
    }
    
    # Count locks
    locks_dir = settings.swarm_root / "LOCKS"
    lock_count = len(list(locks_dir.glob("*.lock"))) if locks_dir.exists() else 0
    
    return {
        "status": "healthy" if all(dirs_exist.values()) else "degraded",
        "wave": state["wave"],
        "directories": dirs_exist,
        "active_zerglings": len(state["active_zerglings"]),
        "pending_tasks": len(state["pending_tasks"]),
        "completed_tasks": len(state["completed_tasks"]),
        "active_locks": lock_count
    }
