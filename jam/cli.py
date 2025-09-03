import sys
import os
import argparse
import asyncio

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
        description="Tessera JAM client node. Performant, clean-room implementation in Python by Chainscore Labs",
        epilog="Examples:\n"
               "  tessera-node                    # Run as validator node (default)\n"
               "  tessera-node --builder          # Run as builder node\n"
               "  tessera-node --fuzzer           # Run as fuzzer target for testing\n"
               "  tessera-node --port 40001       # Override port\n"
               "  tessera-node --fuzzer --socket /tmp/custom.sock  # Custom fuzzer socket",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    p.add_argument("--fuzzer", action="store_true", help="Run as a fuzzer target for conformance testing")
    p.add_argument("--port", type=int, help="Override port from env file")
    
    # Fuzzer-specific options
    p.add_argument("--socket", type=str, default="/tmp/jam_conformance.sock", 
                   help="Unix socket path for fuzzer target (only used with --fuzzer)")
    p.add_argument("--record", type=str, default="fuzzer_session.json",
                   help="Path to record fuzzer session data (only used with --fuzzer)")
    p.add_argument("--no-record", action="store_true",
                   help="Disable session recording (only used with --fuzzer)")
    
    return p

def main():
    # Change to base directory first for file resolution
    base_dir = detect_base_dir()
    os.chdir(base_dir)
    
    parser = build_parser()
    args = parser.parse_args()
    
    # Handle help topics (tessera-node help <topic>)
    if len(sys.argv) >= 3 and sys.argv[1] == "help":
        from jam.utils.clihelpers import show_help_topic
        show_help_topic(sys.argv[2])
        return
    
    # Check for fuzzer mode
    if args.fuzzer:
        print("🎯 Starting Tessera in fuzzer target mode...")
        
        # Import fuzzer functionality
        from jam.fuzzer.target import run_fuzzer_target
        
        # Determine record path
        record_path = None if args.no_record else args.record
        
        # Run fuzzer target
        asyncio.run(
            run_fuzzer_target(
                db_path=args.db,
                socket_path=args.socket,
                record_path=record_path
            )
        )
        return
    
    # Import main function only when needed (faster startup)
    from jam.__main__ import main as node_main
    
    # Set defaults
    if not args.builder and not args.validator and not args.fuzzer:
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
