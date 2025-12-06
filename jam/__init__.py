import argparse
from jam.utils.chainspec import JamConfig, chain_config
import asyncio

__all__ = ["JamConfig", "chain_config"]


def run_jam():
    """Entry point for the node."""
    try:
        from jam.__main__ import main

        # Args parse
        parser = argparse.ArgumentParser(description="Tessera JAM node")
        parser.add_argument("--db", type=str, default="data/tmp", help="Path to database file")
        parser.add_argument(
            "--env",
            type=str,
            default="40000.env",
            help="Path to env file containing required environment variables",
        )
        parser.add_argument("--theme", type=str, default="bitcoin", help="Theme to use for logging")
        parser.add_argument("--builder", action="store_true", help="Flag for builders")
        parser.add_argument("--validator", action="store_true", help="Flag for validators")
        parser.add_argument("--no-rpc", action="store_false", default=True, help="Flag for turning rpc off")
        # Pass on telemetry host:port
        parser.add_argument("--telemetry", type=str, default=None, help="Telemetry host:port")

        args = parser.parse_args()

        asyncio.run(
            main(
                args.db,
                args.env,
                args.theme,
                args.builder,
                args.validator,
                args.no_rpc,
                args.telemetry
            )
        )
    except asyncio.exceptions.CancelledError:
        asyncio.Runner().close()
        print("\nCtrl-C received, Node shutting down!!!!!!")