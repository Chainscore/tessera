import argparse
import uvloop
from .chainspec import JamConfig, chain_config
import asyncio
from jam.__main__ import main

__all__ = ["JamConfig", "chain_config"]

def run_jam():
    """Entry point for the node."""

    # Args parse
    parser = argparse.ArgumentParser(description="JAM node")
    parser.add_argument("--port", type=int, default=30333, help="Port to start server on")
    parser.add_argument("--genesis", type=str, default="genesis.json", help="Path to genesis file")

    args = parser.parse_args()

    uvloop.install()
    asyncio.run(main(args.genesis, args.port))
