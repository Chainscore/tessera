# jam/cli.py

import sys
import os
import argparse
import asyncio
from dotenv import load_dotenv

# Try to import your async entrypoint
try:
    from .__main__ import main as node_main
except (ImportError, SystemError):
    from jam.__main__ import main as node_main  # fallback

def detect_base_dir():
    """
    Return the folder containing your data files:
      - If frozen by PyInstaller, that's _MEIPASS
      - Otherwise, it's the parent of this package (i.e. your project root)
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    pkg_dir = os.path.dirname(__file__)            # .../tessera/jam
    return os.path.abspath(os.path.join(pkg_dir, os.pardir))

def build_parser(base_dir: str):
    p = argparse.ArgumentParser(
        prog="Tessera",
        description="Tessera node CLI: specify node ID and options"
    )
    p.add_argument(
        "node",
        metavar="NODE",
        help=(
            "Node identifier (e.g. 40002) → loads envs/40002.env, "
            "sets PORT and NODE_NAME accordingly"
        )
    )
    p.add_argument(
        "--genesis",
        default=os.path.join(base_dir, "dev-spec.json"),
        help="Path to genesis spec JSON"
    )
    p.add_argument(
        "--start-genesis",
        action="store_true",
        help="Initialize chain from genesis"
    )
    p.add_argument(
        "--theme",
        default="polkadot",
        help="Theme for logging"
    )
    p.add_argument(
        "--builder",
        action="store_true",
        help="Run in builder mode"
    )
    p.add_argument(
        "--validator",
        action="store_true",
        help="Run in validator mode"
    )
    return p

def run_cmd(args):
    # 1) Locate where dev-spec.json, genesis.json and envs/ lives:
    base = detect_base_dir()

    # 2) Change into that folder so bare filenames resolve:
    os.chdir(base)

    # 3) Load environment
    load_dotenv(os.path.join(base, ".env"))
    env_file = os.path.join(base, "envs", f"{args.node}.env")
    load_dotenv(env_file, override=True)

    os.environ.setdefault("PORT",      os.getenv("PORT", args.node))
    os.environ.setdefault("NODE_NAME", os.getenv("NODE_NAME", f"node-{args.node}"))
    os.environ.setdefault("SEED",      os.getenv("SEED", args.node))

    # 4) Dispatch into your async main
    #    Note: __main__.py will still do:
    #        setup_state(..., "dev-spec.json")
    #        json.load(open(genesis_path))
    asyncio.run(
        node_main(
            args.genesis,
            env_file,
            args.start_genesis,
            args.theme,
            args.builder,
            args.validator,
        )
    )

def main():
    base_dir = detect_base_dir()
    parser = build_parser(base_dir)
    args = parser.parse_args()
    run_cmd(args)

if __name__ == "__main__":
    main()
