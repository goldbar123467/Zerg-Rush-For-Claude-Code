"""File locking MCP tools."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from fastmcp import Context
from ..server import mcp
from ..config import settings
from ..flavor import SwarmEvent, emit

LOCKS_DIR = settings.swarm_root / "LOCKS"


def _get_lock_file(path: str) -> Path:
    """Get lock file path for a given file path."""
    safe_name = path.replace("/", "_").replace(".", "_") + ".lock"
    return LOCKS_DIR / safe_name


@mcp.tool(name="lock_acquire", description="Acquire lock on files")
async def lock_acquire(
    ctx: Context,
    paths: list[str],
    holder: str,
    ttl: int = 300
) -> dict:
    """Reserve files for exclusive editing."""
    LOCKS_DIR.mkdir(exist_ok=True)
    acquired = []
    failed = []

    for path in paths:
        lock_file = _get_lock_file(path)
        if lock_file.exists():
            # Check if expired
            data = json.loads(lock_file.read_text())
            if datetime.fromisoformat(data["expires"]) > datetime.now():
                failed.append({"path": path, "holder": data["holder"]})
                continue

        # Create lock
        expires = datetime.now() + timedelta(seconds=ttl)
        lock_data = {
            "path": path,
            "holder": holder,
            "acquired": datetime.now().isoformat(),
            "expires": expires.isoformat()
        }
        lock_file.write_text(json.dumps(lock_data, indent=2))
        acquired.append(path)

    # Emit appropriate voiceline
    voiceline = ""
    if failed:
        voiceline = emit(SwarmEvent.LOCK_CONFLICT, f"[LOCK:{holder}]")
    elif acquired:
        voiceline = emit(SwarmEvent.LOCK_ACQUIRED, f"[LOCK:{holder}]")

    return {"acquired": acquired, "failed": failed, "voiceline": voiceline}


@mcp.tool(name="lock_release", description="Release file locks")
async def lock_release(ctx: Context, paths: list[str], holder: str) -> dict:
    """Release locks held by the specified holder."""
    released = []
    for path in paths:
        lock_file = _get_lock_file(path)
        if lock_file.exists():
            data = json.loads(lock_file.read_text())
            if data["holder"] == holder:
                lock_file.unlink()
                released.append(path)
    return {"released": released}


@mcp.tool(name="lock_check", description="Check if files are locked")
async def lock_check(ctx: Context, paths: list[str]) -> dict:
    """Check lock status of specified files."""
    results = {}
    for path in paths:
        lock_file = _get_lock_file(path)
        if lock_file.exists():
            data = json.loads(lock_file.read_text())
            expired = datetime.fromisoformat(data["expires"]) <= datetime.now()
            results[path] = {"locked": not expired, "holder": data["holder"] if not expired else None}
        else:
            results[path] = {"locked": False, "holder": None}
    return results


@mcp.tool(name="lock_list", description="List all active locks")
async def lock_list(ctx: Context) -> list[dict]:
    """Return all active file locks."""
    locks = []
    if LOCKS_DIR.exists():
        for f in LOCKS_DIR.glob("*.lock"):
            data = json.loads(f.read_text())
            if datetime.fromisoformat(data["expires"]) > datetime.now():
                locks.append(data)
    return locks
