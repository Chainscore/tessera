import argparse
import asyncio
import signal
import sys

from ghost_node import run_node


def handle_sigterm(signum, frame):
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)

    parser = argparse.ArgumentParser()
    # parser.add_argument("--genesis", required=True)
    parser.add_argument("--env", required=True)
    # parser.add_argument("--start-genesis", action="store_true")
    parser.add_argument("--theme", required=True)
    parser.add_argument("--is-builder", action="store_true")
    parser.add_argument("--is-validator", action="store_true")
    args = parser.parse_args()

    asyncio.run(
        run_node(
            env=args.env,
            theme=args.theme,
            is_builder=args.is_builder,
            is_validator=args.is_validator,
        )
    )
