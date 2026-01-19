"""Entry point for running the Zerg Swarm MCP Server."""

import argparse
import json
import sys
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.websockets import WebSocket
from .server import mcp
from .config import settings, init_flavor_config
from . import flavor

# Import all tool modules to register them with the MCP server
from .tools import state, tasks, locks, zergling, wave, results, reconcile


async def get_tool_fn(name: str):
    """Get the underlying function for a tool, bypassing context requirement."""
    tool = await mcp.get_tool(name)
    if tool and hasattr(tool, 'fn'):
        return tool.fn
    return None


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Orson CLI."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                method = request.get("method", "").replace("tools/", "")
                params = request.get("params", {})
                request_id = request.get("id", 0)

                # Get the tool function
                tool_fn = await get_tool_fn(method)

                if tool_fn:
                    try:
                        # Call the function directly, skipping 'ctx' param
                        import inspect
                        sig = inspect.signature(tool_fn)
                        # Filter out 'ctx' parameter if present
                        filtered_params = {k: v for k, v in params.items() if k != 'ctx'}

                        # Check if function needs ctx - if so, pass None
                        if 'ctx' in sig.parameters:
                            result = await tool_fn(ctx=None, **filtered_params)
                        else:
                            result = await tool_fn(**filtered_params)

                        # Handle different return types
                        if hasattr(result, "model_dump"):
                            result = result.model_dump()
                        elif hasattr(result, "__dict__") and not isinstance(result, dict):
                            result = result.__dict__
                        response = {"jsonrpc": "2.0", "result": result, "id": request_id}
                    except Exception as e:
                        response = {
                            "jsonrpc": "2.0",
                            "error": {"code": -32000, "message": str(e)},
                            "id": request_id
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                        "id": request_id
                    }

                await websocket.send_text(json.dumps(response))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None
                }))
    except Exception:
        pass  # Client disconnected


def create_app():
    """Create the combined MCP + WebSocket app."""
    mcp_app = mcp.http_app()

    app = Starlette(
        routes=[
            WebSocketRoute("/ws", websocket_endpoint),
            Mount("/", app=mcp_app),
        ]
    )
    return app


STARTUP_BANNER = """
╔══════════════════════════════════════════════════════════════╗
║  ███████╗███████╗██████╗  ██████╗     ███████╗██╗    ██╗     ║
║  ╚══███╔╝██╔════╝██╔══██╗██╔════╝     ██╔════╝██║    ██║     ║
║    ███╔╝ █████╗  ██████╔╝██║  ███╗    ███████╗██║ █╗ ██║     ║
║   ███╔╝  ██╔══╝  ██╔══██╗██║   ██║    ╚════██║██║███╗██║     ║
║  ███████╗███████╗██║  ██║╚██████╔╝    ███████║╚███╔███╔╝     ║
║  ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝ ╚══╝╚══╝      ║
║                   MCP Server v0.1.0                          ║
╚══════════════════════════════════════════════════════════════╝
"""

STARTUP_VOICELINES = [
    "The Swarm awakens. Your filesystem will never be the same.",
    "Hive mind online. Resistance is futile but also kind of pointless.",
    "Server spawned. Creep spreading. Coffee brewing.",
    "All systems nominal. Existential dread: contained.",
    "MCP Server active. We have control. We have no idea what to do with it.",
    "The Overmind stirs. It smells like... JSON.",
    "Booting up. Please keep all limbs inside the hive at all times.",
]


def main():
    """Start the MCP HTTP server."""
    parser = argparse.ArgumentParser(description="Zerg Swarm MCP Server")
    parser.add_argument(
        "--serious-mode",
        action="store_true",
        help="Disable all flavor text (for demos/investors)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable flavor text output"
    )
    parser.add_argument(
        "--host",
        default=settings.host,
        help=f"Server host (default: {settings.host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Server port (default: {settings.port})"
    )
    args = parser.parse_args()

    # Configure flavor text
    flavor.configure(
        verbose=not args.quiet,
        serious_mode=args.serious_mode
    )

    # Print banner
    if flavor.is_enabled():
        print(STARTUP_BANNER, file=sys.stderr)
        import random
        print(f"[SWARM] {random.choice(STARTUP_VOICELINES)}", file=sys.stderr)
        print("", file=sys.stderr)

    print(f"Starting Zerg Swarm MCP Server on http://{args.host}:{args.port}")
    print(f"WebSocket endpoint: ws://{args.host}:{args.port}/ws")
    print(f"SWARM_ROOT: {settings.swarm_root}")
    print(f"Flavor text: {'disabled (--serious-mode)' if args.serious_mode else ('disabled (--quiet)' if args.quiet else 'enabled')}")
    print("Available tools: swarm_status, task_list, zergling_register, lock_acquire, wave_status, health_check")

    uvicorn.run(
        create_app(),
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
