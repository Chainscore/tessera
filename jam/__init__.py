import argparse
from .chainspec import JamConfig, chain_config
import asyncio
from jam.__main__ import main
# from jam.network.playground.main import main

__all__ = ["JamConfig", "chain_config"]

def run_jam():
    """Entry point for the node."""

    # Args parse
    parser = argparse.ArgumentParser(description="JAM node")
    parser.add_argument("--name", type=str, default="JAM", help="Name of the node")
    parser.add_argument("--port", type=int, default=30333, help="Port to start server on")
    parser.add_argument("--genesis", type=str, default="genesis.json", help="Path to genesis file")
    parser.add_argument("--db", type=str, default="db", help="Path to database file")
    parser.add_argument("--builder", type=bool, default=False, help="Flag for builders")
    parser.add_argument("--validator", type=bool, default=True, help="Flag for validators")
    parser.add_argument("--start-genesis", action="store_true", help="Flag to start from genesis")
    parser.add_argument("--theme", type=str, default="polkadot", help="Theme to use for logging")
    parser.add_argument("--builder", type=bool, default=False, help="Flag for builders")

    args = parser.parse_args()

    asyncio.run(main(args.name, args.genesis, args.db, args.port, args.start_genesis, args.theme, args.builder, args.validator))
