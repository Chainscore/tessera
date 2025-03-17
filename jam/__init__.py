import uvloop
from .chainspec import JamConfig, chain_config
import asyncio
from jam.__main__ import main

__all__ = ["JamConfig", "chain_config"]

def run_jam():
    """Entry point for the application."""
    uvloop.install()
    asyncio.run(main())
