"""Entry point for python -m orson

Usage:
    orson              # Start terminal UI (default)
    orson cli          # Start terminal UI
    orson server       # Start web server
"""

import sys


def main():
    """Main entry point with subcommand support."""
    args = sys.argv[1:]

    if not args or args[0] == "cli":
        from .cli import main as cli_main
        cli_main()
    elif args[0] == "server":
        from .server import main as server_main
        server_main()
    elif args[0] in ("-h", "--help"):
        print(__doc__)
    else:
        print(f"Unknown command: {args[0]}")
        print("Use 'cli' or 'server'")
        sys.exit(1)


if __name__ == "__main__":
    main()
