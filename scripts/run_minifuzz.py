#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import threading
import time
from pathlib import Path


DEFAULT_SOCKET = "/tmp/jam_target.sock"
DEFAULT_MODE = "both"
VALID_MODES = ("both", "no_forks", "forks")
NODE_SHUTDOWN_GRACE_SECONDS = 3


def prompt_with_default(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def prompt_mode(default: str = DEFAULT_MODE) -> str:
    print("Select traces to run:")
    print("  1. both (Recommended)")
    print("  2. no_forks")
    print("  3. forks")
    raw = input(f"Choice [{default}]: ").strip().lower()

    mapping = {
        "": default,
        "1": "both",
        "2": "no_forks",
        "3": "forks",
        "both": "both",
        "forks": "forks",
        "no_forks": "no_forks",
        "no-forks": "no_forks",
        "noforks": "no_forks",
    }
    mode = mapping.get(raw)
    if mode is None:
        raise SystemExit(
            f"Invalid mode {raw!r}. Expected one of: both, no_forks, forks."
        )
    return mode


def q(parts: list[str]) -> str:
    import shlex
    return " ".join(shlex.quote(part) for part in parts)


def ensure_exists(path: Path, label: str) -> Path:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")
    return path


def resolve_tessera_path(run_cwd: Path, raw_value: str) -> Path:
    candidate = Path(raw_value.strip()).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (run_cwd / candidate).resolve()

    if not resolved.exists():
        raise SystemExit(f"Tessera path does not exist: {resolved}")
    if not resolved.is_dir():
        raise SystemExit(f"Tessera path is not a directory: {resolved}")
    if not (resolved / "jam" / "cli.py").exists():
        raise SystemExit(f"Missing jam/cli.py in tessera path: {resolved}")
    return resolved


def tmux_available() -> bool:
    return subprocess.run(
        ["bash", "-lc", "command -v tmux >/dev/null 2>&1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def has_tmux_session(session_name: str) -> bool:
    return subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def print_line() -> None:
    print("-" * 72)


def print_intro() -> None:
    print()
    print("=" * 72)
    print("FUZZ TEST")
    print("=" * 72)


def print_section(title: str) -> None:
    print(f"\n{title}")
    print_line()


def countdown(label: str, seconds: int = 3) -> None:
    print_section(f"Starting {label}")
    for remaining in range(seconds, 0, -1):
        print(f"Opening tmux logs in {remaining}s...", flush=True)
        time.sleep(1)


def dataset_order(mode: str) -> list[str]:
    if mode == "forks":
        return ["forks"]
    if mode == "no_forks":
        return ["no_forks"]
    return ["forks", "no_forks"]


def trace_dir(tessera_root: Path, dataset: str) -> Path:
    return ensure_exists(
        tessera_root
        / "test-suites"
        / "ext"
        / "jam-conformance"
        / "fuzz-proto"
        / "examples"
        / "0.7.2"
        / dataset,
        f"{dataset} traces",
    )


def count_vectors(dataset_dir: Path) -> int:
    return sum(
        1
        for path in dataset_dir.iterdir()
        if path.is_file() and "_fuzzer_" in path.name and path.suffix == ".bin"
    )


def build_minifuzz_cmd(tessera_root: Path, socket_path: Path, dataset: str) -> list[str]:
    minifuzz = ensure_exists(
        tessera_root
        / "test-suites"
        / "ext"
        / "jam-conformance"
        / "fuzz-proto"
        / "minifuzz"
        / "minifuzz.py",
        "minifuzz.py",
    )
    traces = trace_dir(tessera_root, dataset)
    python_cmd = os.environ.get("PYTHON3") or "python3"
    return [
        python_cmd,
        "-u",
        str(minifuzz),
        "-d",
        str(traces),
        "--target-sock",
        str(socket_path),
    ]


def wait_for_socket(socket_path: Path, timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if socket_path.exists():
            return
        time.sleep(0.2)
    raise SystemExit(f"Timed out waiting for socket: {socket_path}")


def open_tmux_logs(dataset: str) -> tuple[str, str, str]:
    session_name = f"jam-minifuzz-{dataset}-{int(time.time())}"
    subprocess.run(["tmux", "new-session", "-d", "-s", session_name, "-n", "logs"], check=True)
    subprocess.run(["tmux", "split-window", "-h", "-t", f"{session_name}:logs"], check=True)
    subprocess.run(["tmux", "select-layout", "-t", f"{session_name}:logs", "even-horizontal"], check=True)
    subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:logs.0", "clear", "C-m"], check=True)
    subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:logs.1", "clear", "C-m"], check=True)
    subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:logs.0", f"echo 'Tessera node logs ({dataset})'", "C-m"], check=True)
    subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:logs.1", f"echo 'Minifuzz logs ({dataset})'", "C-m"], check=True)
    subprocess.run(["tmux", "select-window", "-t", f"{session_name}:logs"], check=True)
    subprocess.run(["tmux", "select-pane", "-t", f"{session_name}:logs.0"], check=True)

    node_tty = subprocess.check_output(
        ["tmux", "display-message", "-p", "-t", f"{session_name}:logs.0", "#{pane_tty}"],
        text=True,
    ).strip()
    fuzz_tty = subprocess.check_output(
        ["tmux", "display-message", "-p", "-t", f"{session_name}:logs.1", "#{pane_tty}"],
        text=True,
    ).strip()
    return session_name, node_tty, fuzz_tty


def write_pane_header(tty_path: str, lines: list[str]) -> None:
    with open(tty_path, "w", encoding="utf-8", buffering=1) as tty:
        for line in lines:
            tty.write(f"{line}\n")
        tty.flush()


def stream_output(
    proc: subprocess.Popen[str],
    tty_path: str,
    buffer: list[str],
    prefix: str | None = None,
) -> None:
    with open(tty_path, "a", encoding="utf-8", buffering=1) as tty:
        if proc.stdout is None:
            return
        for line in proc.stdout:
            if prefix:
                out = f"{prefix}{line}"
            else:
                out = line
            buffer.append(out)
            tty.write(out)
            tty.flush()


def terminate_process(proc: subprocess.Popen[str], timeout: float = 5.0) -> int:
    if proc.poll() is not None:
        return int(proc.returncode)
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=timeout)
    return int(proc.returncode)


def kill_tmux_session_when_done(
    session_name: str,
    node_proc: subprocess.Popen[str],
    fuzz_proc: subprocess.Popen[str],
) -> None:
    fuzz_proc.wait()
    try:
        node_proc.wait(timeout=NODE_SHUTDOWN_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        terminate_process(node_proc)

    if has_tmux_session(session_name):
        subprocess.run(
            ["tmux", "kill-session", "-t", session_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def extract_fuzzer_closed(node_lines: list[str]) -> bool:
    return "fuzzer connection closed" in "".join(node_lines).lower()


def parse_minifuzz(minifuzz_lines: list[str]) -> dict[str, int | bool | None]:
    text = "".join(minifuzz_lines)
    found_match = re.search(r"Found (\d+) fuzzer files to process", text)
    processed = len(re.findall(r"Processing pair \d+:", text))
    unexpected = len(re.findall(r"Unexpected ", text))
    errors = len(re.findall(r"(?m)^Error\b", text))
    connected = "Connected to target socket" in text
    closed = "Connection closed" in text
    return {
        "found": int(found_match.group(1)) if found_match else None,
        "processed": processed,
        "unexpected": unexpected,
        "errors": errors,
        "connected": connected,
        "closed": closed,
    }


def summarize_dataset(
    dataset: str,
    duration_seconds: float,
    vector_count: int,
    node_rc: int,
    fuzz_rc: int,
    node_lines: list[str],
    fuzz_lines: list[str],
) -> None:
    parsed = parse_minifuzz(fuzz_lines)
    found = parsed["found"]
    processed = parsed["processed"]
    unexpected = parsed["unexpected"]
    errors = parsed["errors"]
    passed = (
        fuzz_rc == 0
        and found is not None
        and processed == found
        and unexpected == 0
        and errors == 0
        and bool(parsed["closed"])
    )

    print_section(f"Analysis: {dataset}")
    print(f"dataset result         : {'PASS' if passed else 'FAIL'}")
    print(f"vectors expected       : {vector_count}")
    print(f"pairs found            : {found}")
    print(f"pairs processed        : {processed}")
    print(f"unexpected mismatches  : {unexpected}")
    print(f"errors                 : {errors}")
    print(f"duration               : {duration_seconds:.2f}s")
    print(f"minifuzz exit status   : {fuzz_rc}")
    print(f"node exit status       : {node_rc}")
    print(f"node closed cleanly    : {extract_fuzzer_closed(node_lines)}")


def run_dataset(
    tessera_root: Path,
    socket_path: Path,
    dataset: str,
    vector_count: int,
) -> None:
    if socket_path.exists():
        socket_path.unlink()

    print(f"dataset               : {dataset}")
    print(f"vectors available     : {vector_count}")
    print(f"socket                : {socket_path}")
    print(f"node command          : JAM_LOG_LEVEL={os.environ.get('JAM_LOG_LEVEL', 'debug')} uv run jam/cli.py --fuzzer --socket {socket_path}")
    print(f"minifuzz command      : {q(build_minifuzz_cmd(tessera_root, socket_path, dataset))}")

    session_name, node_tty, fuzz_tty = open_tmux_logs(dataset)
    print(f"tmux session          : {session_name}")
    print("tmux layout           : left=node, right=minifuzz")
    print("manual detach         : Ctrl-b then d")

    write_pane_header(
        node_tty,
        [
            f"Tessera node logs ({dataset})",
            "",
        ],
    )
    write_pane_header(
        fuzz_tty,
        [
            f"Minifuzz logs ({dataset})",
            "",
            "Waiting for tessera socket...",
            "",
        ],
    )

    node_env = os.environ.copy()
    node_env["JAM_LOG_LEVEL"] = node_env.get("JAM_LOG_LEVEL", "debug")
    node_lines: list[str] = []
    fuzz_lines: list[str] = []

    started = time.time()
    node_proc = subprocess.Popen(
        ["uv", "run", "jam/cli.py", "--fuzzer", "--socket", str(socket_path)],
        cwd=tessera_root,
        env=node_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    node_thread = threading.Thread(
        target=stream_output,
        args=(node_proc, node_tty, node_lines),
        daemon=True,
    )
    node_thread.start()

    print("waiting for tessera socket...")
    wait_for_socket(socket_path)
    print("socket ready")

    with open(fuzz_tty, "a", encoding="utf-8", buffering=1) as tty:
        tty.write("Socket ready\n\n")
        tty.flush()

    fuzz_proc = subprocess.Popen(
        build_minifuzz_cmd(tessera_root, socket_path, dataset),
        cwd=tessera_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    fuzz_thread = threading.Thread(
        target=stream_output,
        args=(fuzz_proc, fuzz_tty, fuzz_lines),
        daemon=True,
    )
    fuzz_thread.start()

    session_killer = threading.Thread(
        target=kill_tmux_session_when_done,
        args=(session_name, node_proc, fuzz_proc),
        daemon=True,
    )
    session_killer.start()

    subprocess.run(["tmux", "attach", "-t", session_name], check=False)

    fuzz_rc = int(fuzz_proc.wait())
    fuzz_thread.join(timeout=2)

    try:
        node_rc = int(node_proc.wait(timeout=NODE_SHUTDOWN_GRACE_SECONDS))
    except subprocess.TimeoutExpired:
        node_rc = terminate_process(node_proc)
    node_thread.join(timeout=2)

    session_killer.join(timeout=2)

    summarize_dataset(
        dataset=dataset,
        duration_seconds=time.time() - started,
        vector_count=vector_count,
        node_rc=node_rc,
        fuzz_rc=fuzz_rc,
        node_lines=node_lines,
        fuzz_lines=fuzz_lines,
    )

    if socket_path.exists():
        socket_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Start tessera in fuzzer socket mode and run jam-conformance minifuzz "
            "against forks, no_forks, or both."
        )
    )
    parser.add_argument(
        "--tessera",
        default=None,
        help=(
            "Path to tessera checkout. "
            "Examples: ../tessera, ../tessera-main, /abs/path/to/tessera-main"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=VALID_MODES,
        default=None,
        help="Which trace set to run.",
    )
    parser.add_argument(
        "--socket",
        default=DEFAULT_SOCKET,
        help=f"Socket path to use. Default: {DEFAULT_SOCKET}",
    )
    parser.add_argument(
        "-y",
        action="store_true",
        help="Assume yes. Do not prompt; use defaults and/or provided arguments.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_cwd = Path.cwd().resolve()
    script_tessera_root = Path(__file__).resolve().parents[1]

    if args.y:
        tessera_value = args.tessera or str(script_tessera_root)
        mode = args.mode or DEFAULT_MODE
    else:
        print_intro()
        print(f"run cwd               : {run_cwd}")
        print("Expected usage        : run this from jam-types-py")
        tessera_value = prompt_with_default(
            "Tessera checkout path",
            args.tessera or str(script_tessera_root),
        )
        mode = args.mode or prompt_mode(DEFAULT_MODE)

    tessera_root = resolve_tessera_path(run_cwd, tessera_value)
    socket_path = Path(args.socket).expanduser()

    if not tmux_available():
        raise SystemExit("tmux is required for live split logs, but it was not found in PATH.")

    print_intro()
    print(f"tessera path          : {tessera_root}")
    print(f"socket                : {socket_path}")
    print(f"mode                  : {mode}")

    datasets = dataset_order(mode)
    dataset_counts = {dataset: count_vectors(trace_dir(tessera_root, dataset)) for dataset in datasets}
    for dataset in datasets:
        print(f"testing available {dataset:8} vectors : {dataset_counts[dataset]}")

    for dataset in datasets:
        countdown(dataset, seconds=3)
        run_dataset(
            tessera_root=tessera_root,
            socket_path=socket_path,
            dataset=dataset,
            vector_count=dataset_counts[dataset],
        )

    print_section("Done")
    print("All requested fuzz sets completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
