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
               "  tessera-node                                              # Run as validator node (default)\n"
               "  tessera-node --fuzzer --socket /tmp/custom.sock           # Run as fuzzer target for testing\n"
               "  tessera-node --import /path/to/test_vectors               # Import test vectors from file or directory\n"
               "  tessera-node --env envs.40001.env                         # Override environment\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--env",
        type=str,
        default="envs/40000.env",
        help="Path to env file containing required environment variables",
    )
    p.add_argument("--db", type=str, default="data/tmp", help="Path to database directory")
    p.add_argument("--theme", type=str, default="bitcoin", help="Theme to use for logging")
    p.add_argument("--fuzzer", action="store_true", help="Run as a fuzzer target for conformance testing")
    
    # Fuzzer-specific options
    p.add_argument("--socket", type=str, default="/tmp/jam_conformance.sock", 
                   help="Unix socket path for fuzzer target (only used with --fuzzer)")
    p.add_argument("--record", type=str, default="fuzzer_session.json",
                   help="Path to record fuzzer session data (only used with --fuzzer)")
    p.add_argument("--no-record", action="store_true",
                   help="Disable session recording (only used with --fuzzer)")
    p.add_argument("--import", dest="import_path", type=str,
                   help="Import test vector(s) from file or directory. JSON files are sorted by name.")
    
    return p

def main():
    # Display ASCII art on startup
    ascii_art = """
                                                                             
                                                                            
                                                                            
                                                                      
                                 .......                              
                                ...:::.....                           
                               ..:......::...                      :-.
                       .......   ..::......:.  ..    :.           -#- 
                     ........:::-=-.......... ....   :*.        .==+. 
                    ...::--====-::.  .-.....   ...:. :*+.      :+::+  
                 ..:-===#*-::...     -%=       .-==. :=:+.   .-=. =-  
          ..::-===---::.++....:.    :+-+     .-==:.:.-= :*. .+-  .+.  
        .=+==-:..  .....-#:.::..   .+. +:  .-=-. .::.=-  -*:+:   .+   
         ..        ...::.*-...     =-  :+:==:.   ....+:   -*:    :=   
                     ....=+.      :+. .:**.        ..*.    .     =-   
                         .*.     .+..-=-.+:        .:+           +:   
                    ......*-     ==-=-.  :*.      ..+=          .+.   
                   ..::::.-*... :%+-.     :+.   ..:.*:          .=    
                   .:......*=...-*.        :.   .::.-.          :=    
                   .:....:-+#:.. .             .::..            :=    
                    .:-=+==::.:...            ..:..             :-    
                 .:-===-:....:..   .......... ....              ::    
             .:-===:.   ....... ....::::::::.                   ::    
          .-===-..              .::::::::....                   ::    
      .:-==-:.                  ..........                      ..    
  ..-==-:.                        ...                           ..    
.-==-.                                                           .    By Chainscore Labs
...                                                                   
                                                                      
                                                                      
"""
    print(ascii_art)
    
    # Change to base directory first for file resolution
    base_dir = detect_base_dir()
    os.chdir(base_dir)
    
    parser = build_parser()
    args = parser.parse_args()
    
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
    
    # Check for import mode
    if args.import_path:
        # Setup basic logging for import mode
        from jam.logging import setup_logging
        setup_logging(theme="default", node_name="importer", level="INFO")
        
        print("📥 Starting Tessera in import mode...")
        
        # Import import functionality
        from jam.fuzzer.importer import run_import
        
        # Run importer
        asyncio.run(
            run_import(
                db_path=args.db,
                import_path=args.import_path
            )
        )
        return
    
    # Import main function
    from jam.__main__ import main as node_main
    
    # Run the node
    try:
        asyncio.run(
            node_main(
                args.db,
                args.env, 
                args.theme,
                False,
                True,
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
