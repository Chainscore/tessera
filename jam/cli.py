# jam/cli.py
import sys
import os
import argparse
import asyncio
from dotenv import load_dotenv

# Try to import node_main from your package or fallback to direct load
try:
    from .__main__ import main as node_main
except (ImportError, SystemError):
    try:
        from jam.__main__ import main as node_main
    except ImportError:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "node_main_module",
            os.path.join(os.path.dirname(__file__), "__main__.py")
        )
        node_main_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(node_main_mod)
        node_main = node_main_mod.main


def detect_base_dir():
    """
    Determine project root or PyInstaller unpack dir:
      - If frozen (PyInstaller onefile), use _MEIPASS
      - Else, return parent of the jam/ package (project root)
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    pkg_dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(pkg_dir, os.pardir))


def build_parser(base_dir: str):
    parser = argparse.ArgumentParser(
        prog="Tessera",
        description="Tessera node CLI: specify node ID and options"
    )
    # positional node ID (e.g., 40002)
    parser.add_argument(
        "node",
        metavar="NODE",
        help=("Node identifier (e.g. 40002) → loads envs/40002.env, "
              "sets PORT and NODE_NAME accordingly")
    )
    # run options
    parser.add_argument(
        "--genesis",
        default=os.path.join(base_dir, "dev-spec.json"),
        help="Path to genesis spec JSON"
    )
    parser.add_argument(
        "--start-genesis",
        action="store_true",
        help="Initialize chain from genesis"
    )
    parser.add_argument(
        "--theme",
        default="polkadot",
        help="Theme for logging"
    )
    parser.add_argument(
        "--builder",
        action="store_true",
        help="Run in builder mode"
    )
    parser.add_argument(
        "--validator",
        action="store_true",
        help="Run in validator mode"
    )
    return parser


def run_cmd(args):
    base = detect_base_dir()
    if not os.path.isabs(args.genesis):
        genesis_path = os.path.join(base, args.genesis)
    else:
        genesis_path = args.genesis

    # Load .env files…
    load_dotenv(os.path.join(base, ".env"))
    env_file = os.path.join(base, "envs", f"{args.node}.env")
    load_dotenv(env_file, override=True)
    # Ensure required vars
    os.environ.setdefault("PORT",      os.getenv("PORT", args.node))
    os.environ.setdefault("NODE_NAME", os.getenv("NODE_NAME", f"node-{args.node}"))
    os.environ.setdefault("SEED",      os.getenv("SEED", args.node))

    # Run async main
    asyncio.run(
        node_main(
            genesis_path,
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
