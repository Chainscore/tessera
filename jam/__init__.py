import argparse
import uvloop
from .chainspec import JamConfig, chain_config
import asyncio
from jam.__main__ import main
# from jam.network.playground.main import main

__all__ = ["JamConfig", "chain_config"]

def run_jam():
    """Entry point for the node."""

    # Args parse
    parser = argparse.ArgumentParser(description="JAM node")
    parser.add_argument("--port", type=int, default=30333, help="Port to start server on")
    parser.add_argument("--genesis", type=str, default="genesis.json", help="Path to genesis file")
    parser.add_argument("--db", type=str, default="db", help="Path to database file")
    parser.add_argument("--builder", action="store_true", help="Flag for builders")
    parser.add_argument("--validator", action="store_false", help="Flag for validators")
    parser.add_argument("--start-gen", action="store_true", help="Flag to start from genesis")

    args = parser.parse_args()

    uvloop.install()
    asyncio.run(main(args.genesis, args.db, args.port, args.builder, args.validator, args.start_gen))
    # asyncio.run(main())
