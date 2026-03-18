#!/usr/bin/env python3

import argparse
import socket
import struct
from pathlib import Path

from tsrkit_types import U8, U32, Bytes32, TypedVector, String
from deepdiff import DeepDiff

from jam.fuzzer.constants import (
    TAG_PEER_INFO,
    TAG_INITIALIZE,
    TAG_IMPORT_BLOCK,
    TAG_GET_STATE,
    TAG_STATE_ROOT,
    TAG_STATE,
    TAG_ERROR,
    FEATURE_ANCESTRY,
    FEATURE_FORK,
)

from jam.fuzzer.types import (
    Version,
    PeerInfo,
    Initialize,
    State,
    Ancestry,
    Case,
)

# ============================================================
# CONFIG
# ============================================================

TEST_SPECIFIC = False
IGNORE_STATE_FETCH = True

TRACES_TO_TEST = [
    "1766241968_00000026.bin",
    "1766243861_2056_00000023.bin",
    "1766244122_3562_00000016.bin",
    "1766565819_4337_00000057.bin",
    "1766565819_9942_00000004.bin",
    "1767889897_4774_00002352.bin",
    "1767895984_8315_00001917.bin",
    "1767895984_8315_00001918.bin",
    "1767895984_8315_00001919.bin",
    "1767895984_8315_00001920.bin",
]

# ============================================================
# SOCKET HELPERS
# ============================================================

def send(sock: socket.socket, tag: int, payload: bytes = b""):
    msg = bytes([tag]) + payload
    sock.sendall(struct.pack("<I", len(msg)) + msg)


def recv(sock: socket.socket):
    hdr = sock.recv(4)
    if not hdr:
        return None, None

    length = struct.unpack("<I", hdr)[0]
    buf = b""
    while len(buf) < length:
        chunk = sock.recv(length - len(buf))
        if not chunk:
            return None, None
        buf += chunk

    return buf[0], buf[1:]


# ============================================================
# CONNECTION / HANDSHAKE
# ============================================================

def handshake(sock: socket.socket):
    peer = PeerInfo(
        fuzz_version=U8(1),
        fuzz_features=U32(FEATURE_ANCESTRY | FEATURE_FORK),
        jam_version=Version(U8(0), U8(7), U8(2)),
        app_version=Version(U8(0), U8(1), U8(0)),
        app_name=String("microfuzz"),
    )

    send(sock, TAG_PEER_INFO, peer.encode())
    tag, payload = recv(sock)

    if tag != TAG_PEER_INFO:
        raise RuntimeError("Handshake failed")

    remote = PeerInfo.decode(payload)
    print(f"🤝 Handshake with {remote.app_name}")


def connect_and_handshake(sock_path: str) -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(sock_path)
    handshake(sock)
    return sock


# ============================================================
# TRACE EXECUTION
# ============================================================

def run_trace(sock: socket.socket, case: Case, trace_id: str) -> bool:
    # ---------- INITIALIZE ----------
    init = Initialize(
        header=case.block.header,
        keyvals=State(keyvals=case.pre_state.key_vals),
        ancestry=Ancestry(items=TypedVector([])),
    )

    send(sock, TAG_INITIALIZE, init.encode())
    tag, payload = recv(sock)

    if tag != TAG_STATE_ROOT:
        raise RuntimeError("Initialize failed")

    got_root = Bytes32(payload)
    if got_root != case.pre_state.state_root:
        raise RuntimeError("Init root mismatch")

    print("✅ Initialize OK")

    # ---------- IMPORT BLOCK ----------
    send(sock, TAG_IMPORT_BLOCK, case.block.encode())
    tag, payload = recv(sock)

    mismatch = False

    if tag == TAG_ERROR:
        print("❌ Target returned ERROR")
        mismatch = True

    elif tag == TAG_STATE_ROOT:
        got = Bytes32(payload)
        exp = case.post_state.state_root

        if got == exp:
            print("✅ Block OK")
            return True

        print("❌ Post-state root mismatch")
        mismatch = True

    else:
        raise RuntimeError(f"Protocol violation (tag={tag})")

    # ---------- OPTIONAL STATE FETCH ----------
    if IGNORE_STATE_FETCH:
        print("⏭️  Skipping state fetch (IGNORE_STATE_FETCH=True)")
        return False

    print("🔎 Fetching state for diff…")
    send(sock, TAG_GET_STATE)

    tag, payload = recv(sock)
    if tag != TAG_STATE:
        raise RuntimeError("Failed to fetch state")

    actual = State.decode(payload)

    actual_kv = {kv.key.hex(): kv.value.hex() for kv in actual.keyvals}
    expected_kv = {
        kv.key.hex(): kv.value.hex()
        for kv in case.post_state.key_vals
    }

    diff = DeepDiff(actual_kv, expected_kv, view="tree")

    if diff:
        print("📛 KV DIFF:")
        for k, v in expected_kv.items():
            if k not in actual_kv:
                print(f"  ❌ Missing key: {k}")
            elif actual_kv[k] != v:
                print(f"  ❌ Value mismatch [{k}]")
                print(f"     Exp: {v}")
                print(f"     Act: {actual_kv[k]}")
    else:
        print("⚠️ No KV diff despite root mismatch")

    return False


# ============================================================
# TRACE DISCOVERY / LOADING
# ============================================================

def discover_traces(trace_dir: Path) -> list[str]:
    traces = []
    for mod in trace_dir.iterdir():
        if not mod.is_dir():
            continue
        for f in mod.glob("*.bin"):
            traces.append(f"{mod.name}_{f.name}")
    return sorted(traces)


def load_case(trace_dir: Path, trace_id: str) -> Case | None:
    module, file = trace_id.rsplit("_", 1)

    if file.startswith("genesis"):
        return None

    path = trace_dir / module / file
    return Case.decode(path.read_bytes())


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", required=True)
    parser.add_argument("--target-sock", required=True)
    args = parser.parse_args()

    trace_dir = Path(args.trace_dir)

    trace_ids = TRACES_TO_TEST if TEST_SPECIFIC else discover_traces(trace_dir)

    passed = 0
    failed: list[str] = []

    sock = connect_and_handshake(args.target_sock)

    for trace_id in trace_ids:
        print("\n==============================")
        print(f"▶ Running {trace_id}")

        case = load_case(trace_dir, trace_id)
        if case is None:
            print("⏭️  Skipping genesis")
            continue

        try:
            ok = run_trace(sock, case, trace_id)
            if ok:
                passed += 1
                print("✅ Trace OK")
            else:
                failed.append(trace_id)
                raise RuntimeError("Trace failed")

        except Exception as e:
            print(f"💥 Exception: {e}")
            failed.append(trace_id)

            # 🔁 Reset connection cleanly
            try:
                sock.close()
            except Exception:
                pass

            sock = connect_and_handshake(args.target_sock)

    try:
        sock.close()
    except Exception:
        pass

    # ---------- SUMMARY ----------
    executed = passed + len(failed)

    print("\n==============================")
    print("📊 FUZZ SUMMARY")
    print(f"Total executed: {executed}")
    print(f"Passed:         {passed}")
    print(f"Failed:         {len(failed)}")

    if failed:
        print("\nFailures:")
        for f in failed:
            print(f"  ❌ {f}")


if __name__ == "__main__":
    main()
