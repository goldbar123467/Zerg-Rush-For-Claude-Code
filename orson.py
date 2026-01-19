#!/usr/bin/env python3
"""
Orson Agent IDE Launcher

Usage:
    python orson.py [--port PORT] [--host HOST]

Examples:
    python orson.py                    # Start on localhost:8000
    python orson.py --port 3000        # Custom port
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orson.server import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Orson Agent IDE - The hive wears flannel"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )

    args = parser.parse_args()
    main(host=args.host, port=args.port)
