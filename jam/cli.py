# jam/cli.py

import sys
import os
import argparse
import asyncio
from dotenv import load_dotenv

def detect_base_dir():
    """
    Detect the base directory whether running from source or frozen binary.
    Compatible with Nuitka and PyInstaller.
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    pkg_dir = os.path.dirname(__file__)            # .../tessera/jam
    return os.path.abspath(os.path.join(pkg_dir, os.pardir))

def build_parser():
    p = argparse.ArgumentParser(
        prog="tessera-node",
        description="Tessera JAM blockchain node"
    )
    p.add_argument("--db", type=str, default="data/tmp", help="Path to database directory")
    p.add_argument(
        "--env",
        type=str,
        default="envs/40000.env",
        help="Path to env file containing required environment variables",
    )
    p.add_argument("--theme", type=str, default="bitcoin", help="Theme to use for logging")
    p.add_argument("--builder", action="store_true", help="Run as a builder node")
    p.add_argument("--validator", action="store_true", help="Run as a validator node (default)")
    p.add_argument("--port", type=int, help="Override port from env file")
    p.add_argument("--help-topics", action="store_true", help="Show available help topics")
    return p

def main():
    # Change to base directory first for file resolution
    base_dir = detect_base_dir()
    os.chdir(base_dir)
    
    parser = build_parser()
    args = parser.parse_args()
    
    # Handle help topics
    if args.help_topics:
        print("Available help topics:")
        print("  getting-started  - Basic usage and setup")
        print("  networking       - Network configuration") 
        print("  validation       - Validator setup")
        print("  building         - Builder node setup")
        print("\nUse: tessera-node help <topic>")
        return
    
    # Handle help topics (tessera-node help <topic>)
    if len(sys.argv) >= 3 and sys.argv[1] == "help":
        from jam.utils.clihelpers import show_help_topic
        show_help_topic(sys.argv[2])
        return
    
    # Import main function only when needed (faster startup)
    from jam.__main__ import main as node_main
    
    # Set defaults
    if not args.builder and not args.validator:
        args.validator = True
    
    # Override port in environment if specified
    if args.port:
        os.environ["PORT"] = str(args.port)
    
    # Run the node
    try:
        asyncio.run(
            node_main(
                args.db,
                args.env, 
                args.theme,
                args.builder,
                args.validator,
            )
        )
    except KeyboardInterrupt:
        print("\n🛑 Tessera node stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
