"""Zergling lifecycle MCP tools."""

from datetime import datetime
from fastmcp import Context
from ..server import mcp
from .state import _load_state, _save_state


@mcp.tool(name="zergling_register", description="Register a new zergling")
async def zergling_register(ctx: Context, name: str) -> dict:
    """Register an active zergling with the swarm."""
    state = _load_state()
    
    # Check if already registered
    for z in state["active_zerglings"]:
        if z.get("name") == name:
            return {"status": "already_registered", "zergling": z}
    
    entry = {
        "name": name,
        "registered": datetime.now().isoformat(),
        "wave": state["wave"]
    }
    state["active_zerglings"].append(entry)
    _save_state(state)
    
    return {"status": "registered", "zergling": entry}


@mcp.tool(name="zergling_unregister", description="Unregister a zergling")
async def zergling_unregister(ctx: Context, name: str) -> dict:
    """Remove a zergling from active list."""
    state = _load_state()
    
    original_count = len(state["active_zerglings"])
    state["active_zerglings"] = [
        z for z in state["active_zerglings"] 
        if z.get("name") != name
    ]
    
    if len(state["active_zerglings"]) < original_count:
        _save_state(state)
        return {"status": "unregistered", "name": name}
    
    return {"status": "not_found", "name": name}


@mcp.tool(name="zergling_list", description="List active zerglings")
async def zergling_list(ctx: Context) -> list[dict]:
    """Return all active zerglings with their metadata."""
    state = _load_state()
    return state["active_zerglings"]


@mcp.tool(name="zergling_get", description="Get zergling info")
async def zergling_get(ctx: Context, name: str) -> dict:
    """Get details about a specific zergling."""
    state = _load_state()
    
    for z in state["active_zerglings"]:
        if z.get("name") == name:
            return {"status": "found", "zergling": z}
    
    return {"status": "not_found", "name": name}
