"""Task management MCP tools."""

from pathlib import Path
from fastmcp import Context
from ..server import mcp
from ..config import settings

TASKS_DIR = settings.swarm_root / "TASKS"
LANES = ["KERNEL", "ML", "QUANT", "DEX", "INTEGRATION"]


@mcp.tool(name="task_list", description="List tasks by lane or status")
async def task_list(ctx: Context, lane: str = None) -> list[dict]:
    """List task cards, optionally filtered by lane."""
    tasks = []
    lanes_to_scan = [lane] if lane and lane in LANES else LANES
    
    for ln in lanes_to_scan:
        lane_dir = TASKS_DIR / ln
        if lane_dir.exists():
            for f in lane_dir.glob("*.md"):
                if f.name != "README.md":
                    tasks.append({
                        "task_id": f.stem,
                        "lane": ln,
                        "path": str(f)
                    })
    return tasks


@mcp.tool(name="task_get", description="Get a specific task card")
async def task_get(ctx: Context, task_id: str, lane: str) -> dict:
    """Read and return a task card's contents."""
    task_file = TASKS_DIR / lane / f"{task_id}.md"
    if not task_file.exists():
        return {"error": f"Task {lane}/{task_id} not found"}
    
    content = task_file.read_text()
    return {
        "task_id": task_id,
        "lane": lane,
        "content": content
    }


@mcp.tool(name="task_create", description="Create a new task card")
async def task_create(
    ctx: Context, 
    task_id: str, 
    lane: str, 
    task_type: str, 
    objective: str
) -> dict:
    """Create a new task card in the specified lane."""
    if lane not in LANES:
        return {"error": f"Invalid lane: {lane}"}
    
    lane_dir = TASKS_DIR / lane
    lane_dir.mkdir(exist_ok=True)
    task_file = lane_dir / f"{task_id}.md"
    
    content = f"""# Task: {task_id}

## Metadata
| Field | Value |
|-------|-------|
| Lane | {lane} |
| Type | {task_type} |
| Wave | - |
| Status | PENDING |
| Created | {__import__('datetime').datetime.now().strftime('%Y-%m-%d')} |
| Assigned | - |

## Objective
{objective}

## Deliverables
- [ ] TBD

## Constraints
- Max 100 lines
- Max 2 files
"""
    task_file.write_text(content)
    return {"status": "created", "path": str(task_file)}
