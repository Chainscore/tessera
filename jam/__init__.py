import argparse
from jam.utils.chainspec import JamConfig, chain_config
import asyncio

__all__ = ["JamConfig", "chain_config"]


def run_jam():
    """Entry point for the node."""
    from jam.cli import main
    main()