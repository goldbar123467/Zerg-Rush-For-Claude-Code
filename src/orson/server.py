"""
Orson Agent IDE - FastAPI Static Server

A web-based IDE for the Zerg Rush MCP swarm system.
Theme: Midwestern small town meets Starcraft Zerg.

Run: python -m orson or python orson.py
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Paths
ORSON_ROOT = Path(__file__).parent
STATIC_DIR = ORSON_ROOT / "static"
PROJECT_ROOT = ORSON_ROOT.parent.parent  # src/orson -> src -> zerg-swarm
SWARM_ROOT = PROJECT_ROOT / "SWARM"

# App
app = FastAPI(
    title="Orson Agent IDE",
    description="The hive wears flannel.",
    version="0.1.0"
)

# CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Pydantic Models ===

class SwarmState(BaseModel):
    wave: int = 0
    active_zerglings: List[dict] = []
    completed_tasks: List[str] = []
    pending_tasks: List[str] = []
    last_updated: Optional[str] = None


class TaskInfo(BaseModel):
    id: str
    lane: str
    type: Optional[str] = None
    status: Optional[str] = "PENDING"
    content: Optional[str] = None


# === Helper Functions ===

def get_state_path() -> Path:
    return SWARM_ROOT / "STATE.json"


def read_state() -> dict:
    """Read the current swarm state from STATE.json."""
    state_path = get_state_path()
    if not state_path.exists():
        return {
            "wave": 0,
            "active_zerglings": [],
            "completed_tasks": [],
            "pending_tasks": [],
            "last_updated": None
        }
    with open(state_path, "r") as f:
        return json.load(f)


def write_state(state: dict):
    """Write state to STATE.json atomically."""
    state_path = get_state_path()
    state["last_updated"] = datetime.now().isoformat()
    temp_path = state_path.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(state, f, indent=2)
    temp_path.rename(state_path)


def get_tasks_for_lane(lane: str) -> List[dict]:
    """Get all tasks for a specific lane."""
    tasks_dir = SWARM_ROOT / "TASKS" / lane
    if not tasks_dir.exists():
        return []

    tasks = []
    for task_file in tasks_dir.glob("*.md"):
        task_id = task_file.stem
        content = task_file.read_text()

        # Parse basic info from content
        task_type = "TASK"
        status = "PENDING"

        for line in content.split("\n"):
            if "| Type |" in line or "Type:" in line:
                task_type = line.split("|")[-2].strip() if "|" in line else line.split(":")[-1].strip()
            if "| Status |" in line or "Status:" in line:
                status = line.split("|")[-2].strip() if "|" in line else line.split(":")[-1].strip()

        tasks.append({
            "id": task_id,
            "lane": lane,
            "type": task_type,
            "status": status
        })

    return tasks


def list_inbox() -> List[str]:
    """List all results in INBOX."""
    inbox_dir = SWARM_ROOT / "INBOX"
    if not inbox_dir.exists():
        return []
    return [f.stem.replace("_RESULT", "") for f in inbox_dir.glob("*_RESULT.md")]


def list_locks() -> List[dict]:
    """List all active locks."""
    locks_dir = SWARM_ROOT / "LOCKS"
    if not locks_dir.exists():
        return []

    locks = []
    now = datetime.now()
    for lock_file in locks_dir.glob("*.lock"):
        try:
            data = json.loads(lock_file.read_text())
            # Check if expired
            if "expires" in data:
                expires = datetime.fromisoformat(data["expires"])
                if expires < now:
                    continue
            locks.append(data)
        except (json.JSONDecodeError, KeyError):
            continue

    return locks


# === API Endpoints ===

@app.get("/")
async def root():
    """Serve the main IDE page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    state_exists = get_state_path().exists()
    swarm_exists = SWARM_ROOT.exists()

    return {
        "status": "ok" if state_exists and swarm_exists else "degraded",
        "swarm_root": str(SWARM_ROOT),
        "state_exists": state_exists,
        "swarm_exists": swarm_exists,
        "message": "Welcome to Orson, population: variable"
    }


@app.get("/api/swarm/status")
async def swarm_status():
    """Get current swarm state."""
    return read_state()


@app.post("/api/swarm/reset")
async def swarm_reset():
    """Reset swarm state."""
    state = {
        "wave": 0,
        "active_zerglings": [],
        "completed_tasks": [],
        "pending_tasks": []
    }
    write_state(state)
    return {"status": "reset", "state": state}


@app.get("/api/tasks")
async def task_list(lane: Optional[str] = None):
    """List tasks, optionally filtered by lane."""
    lanes = ["KERNEL", "ML", "QUANT", "DEX", "INTEGRATION"]

    if lane:
        if lane.upper() not in lanes:
            raise HTTPException(status_code=400, detail=f"Invalid lane: {lane}")
        return get_tasks_for_lane(lane.upper())

    # Return all tasks grouped by lane
    all_tasks = {}
    for l in lanes:
        all_tasks[l] = get_tasks_for_lane(l)
    return all_tasks


@app.get("/api/tasks/{lane}/{task_id}")
async def task_get(lane: str, task_id: str):
    """Get a specific task."""
    task_path = SWARM_ROOT / "TASKS" / lane.upper() / f"{task_id}.md"
    if not task_path.exists():
        raise HTTPException(status_code=404, detail=f"Task not found: {lane}/{task_id}")

    return {
        "id": task_id,
        "lane": lane.upper(),
        "content": task_path.read_text()
    }


@app.get("/api/zerglings")
async def zergling_list():
    """List active zerglings."""
    state = read_state()
    return state.get("active_zerglings", [])


@app.post("/api/zerglings/{name}")
async def zergling_register(name: str):
    """Register a new zergling."""
    state = read_state()
    zerglings = state.get("active_zerglings", [])

    # Check if already registered
    if any(z["name"] == name for z in zerglings):
        return {"status": "already_registered", "name": name}

    zerglings.append({
        "name": name,
        "registered": datetime.now().isoformat(),
        "wave": state.get("wave", 0)
    })

    state["active_zerglings"] = zerglings
    write_state(state)

    return {"status": "registered", "name": name, "wave": state["wave"]}


@app.delete("/api/zerglings/{name}")
async def zergling_unregister(name: str):
    """Unregister a zergling."""
    state = read_state()
    zerglings = state.get("active_zerglings", [])

    state["active_zerglings"] = [z for z in zerglings if z["name"] != name]
    write_state(state)

    return {"status": "unregistered", "name": name}


@app.get("/api/locks")
async def lock_list():
    """List active file locks."""
    return list_locks()


@app.get("/api/wave")
async def wave_status():
    """Get current wave status."""
    state = read_state()
    return {
        "wave": state.get("wave", 0),
        "active_zerglings": len(state.get("active_zerglings", [])),
        "pending_tasks": len(state.get("pending_tasks", [])),
        "completed_tasks": len(state.get("completed_tasks", []))
    }


@app.post("/api/wave/increment")
async def wave_increment():
    """Increment wave counter."""
    state = read_state()
    old_wave = state.get("wave", 0)
    state["wave"] = old_wave + 1
    write_state(state)

    return {
        "old_wave": old_wave,
        "new_wave": state["wave"]
    }


@app.post("/api/wave/collect")
async def wave_collect():
    """Collect results from INBOX."""
    state = read_state()
    inbox_results = list_inbox()

    # Add to completed tasks
    completed = set(state.get("completed_tasks", []))
    new_completed = 0

    for result in inbox_results:
        if result not in completed:
            completed.add(result)
            new_completed += 1

    state["completed_tasks"] = list(completed)
    write_state(state)

    return {
        "collected": new_completed,
        "total_completed": len(completed)
    }


@app.get("/api/inbox")
async def inbox_list():
    """List results in INBOX."""
    return list_inbox()


@app.get("/api/inbox/{task_id}")
async def result_get(task_id: str):
    """Get a specific result."""
    result_path = SWARM_ROOT / "INBOX" / f"{task_id}_RESULT.md"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail=f"Result not found: {task_id}")

    return {
        "task_id": task_id,
        "content": result_path.read_text()
    }


# Mount static files AFTER API routes to avoid path conflicts
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main(host: str = "127.0.0.1", port: int = 8000):
    """Start the Orson IDE server."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ██████╗ ██████╗ ███████╗ ██████╗ ███╗   ██╗              ║
    ║    ██╔═══██╗██╔══██╗██╔════╝██╔═══██╗████╗  ██║              ║
    ║    ██║   ██║██████╔╝███████╗██║   ██║██╔██╗ ██║              ║
    ║    ██║   ██║██╔══██╗╚════██║██║   ██║██║╚██╗██║              ║
    ║    ╚██████╔╝██║  ██║███████║╚██████╔╝██║ ╚████║              ║
    ║     ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝              ║
    ║                                                               ║
    ║            🌽 AGENT IDE - "The hive wears flannel" 🌽         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"    Starting Orson IDE at http://{host}:{port}")
    print(f"    SWARM directory: {SWARM_ROOT}")
    print()

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
