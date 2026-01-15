"""Entry point for running the Zerg Swarm MCP Server."""

import uvicorn
from .server import mcp
from .config import settings

# Import all tool modules to register them with the MCP server
from .tools import state, tasks, locks, zergling, wave, results, reconcile


def main():
    """Start the MCP HTTP server."""
    print(f"Starting Zerg Swarm MCP Server on http://{settings.host}:{settings.port}")
    print(f"SWARM_ROOT: {settings.swarm_root}")
    print("Available tools: swarm_status, task_list, zergling_register, lock_acquire, wave_status, health_check")
    
    uvicorn.run(
        mcp.http_app(),
        host=settings.host,
        port=settings.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
