
from dotenv import load_dotenv

from .config.chainspec import JamConfig, chain_config
# import asyncio

__all__ = ["JamConfig", "chain_config"]

def run_jam():
    """Entry point for the node."""
    # delegate entirely to jam.cli.main()
    from .cli import main
    main()
