# jam/cli.py

from ast import arg
from logging import Logger
import sys
import os
import json
import argparse
import asyncio
from dotenv import load_dotenv
from jam.__main__ import main as node_main
from jam.config.logging import get_logger


logger=get_logger("cli")

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
    # positional validator index (e.g. 2)
    p.add_argument(
        "--validator_index",
        type=int,
        metavar="Validator Index",
        help="Validator index (e.g. 2). Port and env file derived as 4000{validator_index}."
    )
    p.add_argument(
        "--port",
        type=int,
        help="Port for the node to run"
    )
    p.add_argument(
        "--rpc_port",
        help="RPC port for the rpc to running on that port"
    )
    p.add_argument(
        "--genesis",
        default=os.path.join(base_dir, "dev-spec.json"),
        help="Path to genesis spec JSON"
    )
    p.add_argument(
        "--chain_spec",
        default="tiny",
        help="Setting the chain Specifications"
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
        "--temp_db",
        action="store_true",
        help="Initialize chain from genesis"
    )
    # Mutually exclusive group: only one can be true
    mode_group = p.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--builder",
        action="store_true",
        help="Run in builder mode"
    )
    mode_group.add_argument(
        "--validator",
        action="store_true",
        help="Run in validator mode (default)"
    )
    return p

def run_cmd(args):
    # 1) Locate where dev-spec.json, genesis.json and envs/ lives:
    base = detect_base_dir()

    # 2) Change into that folder so bare filenames resolve:
    os.chdir(base)
    port=40000+args.validator_index

    # 3) Load environment
    load_dotenv(os.path.join(base, ".env"))
    env_file = os.path.join(base, "envs", f"{port}.env")
    load_dotenv(env_file, override=True)

    os.environ["PORT"]=str(args.port if args.port is not None else port)
    if args.temp_db:
        os.environ["TEMPDB"]=str(args.temp_db)
    os.environ["JAM_CHAIN_SPEC"]=str(args.chain_spec)
    os.environ.setdefault("NODE_NAME", os.getenv("NODE_NAME", f"node-{port}"))
    os.environ.setdefault("SEED",      os.getenv("SEED", port))
    if args.rpc_port is not None:
        os.environ.setdefault("RPC_PORT",os.getenv("RPC_PORT", args.rpc_port))
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
