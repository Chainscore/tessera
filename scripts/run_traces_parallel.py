#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import argparse
import contextlib
import importlib
import io
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_SUITES_ROOT = ROOT / "test-suites"
SKIP_FILENAMES = {"00000000.json", "genesis.json", "genesis.bin"}


@dataclass
class TraceResult:
    path: str
    ok: bool
    duration_s: float
    error: str | None = None
    output: str = ""


def _load_trace_harness():
    if str(TEST_SUITES_ROOT) not in sys.path:
        sys.path.insert(0, str(TEST_SUITES_ROOT))
    return importlib.import_module("harness.w3f.traces.test_traces_unified")


def discover_trace_files(module: str | None, pattern: str) -> list[Path]:
    harness = _load_trace_harness()
    files = [
        path for path in harness.get_trace_files(module or "*", pattern)
        if path.name not in SKIP_FILENAMES
    ]
    return sorted(files)


def run_one_trace(path_str: str, db_base: str, rpc: bool, verbose: bool) -> TraceResult:
    os.environ.setdefault("JAM_LOG_LEVEL", "error")
    os.environ.setdefault("JAM_LOG_LEVEL_BLOCK", "error")
    os.environ.setdefault("JAM_LOG_LEVEL_NODE", "error")
    os.environ.setdefault("JAM_LOG_LEVEL_NETWORK", "error")
    os.environ.setdefault("JAM_LOG_LEVEL_PVM", "error")

    harness = _load_trace_harness()
    path = Path(path_str)
    started = time.perf_counter()
    stream = io.StringIO()

    try:
        case = harness.load_trace_case(path)

        async def _run_case() -> None:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                harness.run_transition_check(case, db_base, rpc)

        asyncio.run(_run_case())
        return TraceResult(
            path=str(path),
            ok=True,
            duration_s=time.perf_counter() - started,
            output=stream.getvalue() if verbose else "",
        )
    except Exception as exc:
        details = traceback.format_exc()
        return TraceResult(
            path=str(path),
            ok=False,
            duration_s=time.perf_counter() - started,
            error=str(exc),
            output=stream.getvalue() + details,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run W3F trace harness cases in parallel. "
            "This uses the same discovery and transition logic as "
            "test_traces_unified.py, but executes trace files across multiple processes."
        )
    )
    parser.add_argument(
        "--module",
        default=None,
        help="Trace module/session filter. Defaults to all modules.",
    )
    parser.add_argument(
        "--pattern",
        default="*.json",
        help='Trace file pattern. Use "all" to include both .bin and .json files.',
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=max(1, (os.cpu_count() or 1) - 1),
        help="Maximum number of worker processes.",
    )
    parser.add_argument(
        "--db-path",
        default="data/tmp-traces-parallel",
        help="Base directory for temporary trace databases.",
    )
    parser.add_argument(
        "--no-rpc",
        action="store_false",
        dest="rpc",
        default=True,
        help="Disable RPC during trace execution.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print captured output for successful traces as well.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop scheduling more work after the first failure is observed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = discover_trace_files(args.module, args.pattern)

    if not files:
        print("No trace files matched the requested filters.")
        return 0

    jobs = max(1, min(args.jobs, len(files)))
    db_base = str((ROOT / args.db_path).resolve()) if not Path(args.db_path).is_absolute() else args.db_path
    Path(db_base).mkdir(parents=True, exist_ok=True)

    print(f"Discovered {len(files)} trace files")
    print(f"module={args.module or '*'} pattern={args.pattern} jobs={jobs} rpc={args.rpc}")
    print(f"db_base={db_base}")
    print("")

    started = time.perf_counter()
    passed = 0
    failed = 0
    failures: list[TraceResult] = []

    with ProcessPoolExecutor(max_workers=jobs) as pool:
        future_map = {
            pool.submit(run_one_trace, str(path), db_base, args.rpc, args.verbose): path
            for path in files
        }

        for index, future in enumerate(as_completed(future_map), start=1):
            result = future.result()
            rel_path = Path(result.path).relative_to(ROOT)

            if result.ok:
                passed += 1
                print(
                    f"[{index}/{len(files)}] PASS {rel_path} "
                    f"({result.duration_s:.2f}s)"
                )
                if args.verbose and result.output.strip():
                    print(result.output.rstrip())
                    print("")
            else:
                failed += 1
                failures.append(result)
                print(
                    f"[{index}/{len(files)}] FAIL {rel_path} "
                    f"({result.duration_s:.2f}s): {result.error}"
                )
                if result.output.strip():
                    print(result.output.rstrip())
                    print("")
                if args.fail_fast:
                    for pending in future_map:
                        pending.cancel()
                    break

    total = time.perf_counter() - started
    print("=" * 72)
    print(
        f"Done in {total:.2f}s | total={len(files)} passed={passed} failed={failed}"
    )
    print("=" * 72)

    if failures:
        print("Failures:")
        for item in failures:
            rel_path = Path(item.path).relative_to(ROOT)
            print(f"- {rel_path}: {item.error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
