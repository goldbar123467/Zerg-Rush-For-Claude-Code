"""Entry point for running the Zerg Swarm MCP Server."""

import argparse
import sys
import uvicorn
from .server import mcp
from .config import settings, init_flavor_config
from . import flavor

# Import all tool modules to register them with the MCP server
from .tools import state, tasks, locks, zergling, wave, results, reconcile


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
    print(f"SWARM_ROOT: {settings.swarm_root}")
    print(f"Flavor text: {'disabled (--serious-mode)' if args.serious_mode else ('disabled (--quiet)' if args.quiet else 'enabled')}")
    print("Available tools: swarm_status, task_list, zergling_register, lock_acquire, wave_status, health_check")

    uvicorn.run(
        mcp.http_app(),
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
