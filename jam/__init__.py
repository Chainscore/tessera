import argparse
from jam.utils.chainspec import JamConfig, chain_config
import asyncio

__all__ = ["JamConfig", "chain_config"]


def run_jam():
    """Entry point for the node."""
    from jam.__main__ import main

    # Args parse
    parser = argparse.ArgumentParser(description="JAM node")
    parser.add_argument(
        "--genesis", type=str, default="dev-spec.json", help="Path to genesis file"
    )
    # parser.add_argument("--db", type=str, default="db", help="Path to database file")
    parser.add_argument(
        "--env",
        type=str,
        default="40000.env",
        help="Path to env file containing required environment variables",
    )
    parser.add_argument(
        "--start-genesis", action="store_true", help="Flag to start from genesis"
    )
    parser.add_argument(
        "--theme", type=str, default="polkadot", help="Theme to use for logging"
    )
    parser.add_argument("--builder", action="store_true", help="Flag for builders")
    parser.add_argument("--validator", action="store_true", help="Flag for validators")

    args = parser.parse_args()

    asyncio.run(
        main(
            args.genesis,
            # args.db,
            args.env,
            args.start_genesis,
            args.theme,
            args.builder,
            args.validator,
        )
    )
