"""Result processing MCP tools."""

from datetime import datetime
from pathlib import Path
from fastmcp import Context
from ..server import mcp
from ..config import settings

INBOX_DIR = settings.swarm_root / "INBOX"
OUTBOX_DIR = settings.swarm_root / "OUTBOX"


@mcp.tool(name="result_get", description="Get a task result")
async def result_get(ctx: Context, task_id: str) -> dict:
    """Read a result file from INBOX."""
    result_file = INBOX_DIR / f"{task_id}_RESULT.md"
    if not result_file.exists():
        return {"error": f"Result for {task_id} not found"}
    
    return {
        "task_id": task_id,
        "content": result_file.read_text()
    }


@mcp.tool(name="inbox_list", description="List INBOX contents")
async def inbox_list(ctx: Context) -> list[dict]:
    """List all result files in INBOX directory."""
    results = []
    if INBOX_DIR.exists():
        for f in INBOX_DIR.glob("*.md"):
            results.append({
                "filename": f.name,
                "task_id": f.stem.replace("_RESULT", ""),
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    return results


@mcp.tool(name="outbox_list", description="List OUTBOX contents")
async def outbox_list(ctx: Context) -> list[dict]:
    """List all pending task files in OUTBOX directory."""
    tasks = []
    if OUTBOX_DIR.exists():
        for f in OUTBOX_DIR.glob("*.md"):
            tasks.append({
                "filename": f.name,
                "task_id": f.stem,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    return tasks


@mcp.tool(name="result_submit", description="Submit a task result")
async def result_submit(
    ctx: Context, 
    task_id: str, 
    status: str, 
    summary: str
) -> dict:
    """Write a result file to INBOX."""
    INBOX_DIR.mkdir(exist_ok=True)
    result_file = INBOX_DIR / f"{task_id}_RESULT.md"
    
    content = f"""# Result: {task_id}

## Status
{status}

## Summary
{summary}

## Timestamp
{datetime.now().isoformat()}
"""
    result_file.write_text(content)
    return {"status": "submitted", "path": str(result_file)}
