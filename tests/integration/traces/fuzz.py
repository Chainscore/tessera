"""
fuzz.py - Test trace files against a target using the JAM Fuzzing Protocol.

Similar to minifuzz.py but reads trace files (the same .bin files used by
test_traces_unified.py) and replays them over the fuzzing protocol socket.

For each trace file it:
  1. Connects and handshakes with the target
  2. Sends Initialize (pre_state from the trace + genesis header)
  3. Sends ImportBlock (the block from the trace)
  4. Compares the returned state_root with the expected post_state root

Usage:
  uv run python tests/integration/traces/fuzz.py -d "tessera/test-suites/ext/jam-conformance/fuzz-reports/0.7.2/traces/" -p "*.bin" --target-sock /tmp/jam_conformance.sock -v -m "*"
"""

import argparse
import json
import socket
import struct
import sys
from pathlib import Path

from tsrkit_types import Bytes, Bytes32, U8, U32, TypedVector, String, structure

from jam.block.block import Block
from jam.block.header import Header
from jam.utils.trie.merkle import StateTrie

from jam.fuzzer.types import (
    PeerInfo, Version, Initialize, State, KeyValue,
    Ancestry, AncestryItem, ErrorMessage,
)
from jam.fuzzer.constants import (
    TAG_PEER_INFO,
    TAG_INITIALIZE,
    TAG_STATE_ROOT,
    TAG_IMPORT_BLOCK,
    TAG_GET_STATE,
    TAG_STATE,
    TAG_ERROR,
    FEATURE_ANCESTRY,
    FEATURE_FORK,
)

@structure
class KeyVal:
    key: Bytes[31]
    value: Bytes

@structure
class StateKeyVals:
    state_root: Bytes[32]
    keyvals: TypedVector[KeyVal]

@structure
class Trace:
    pre_state: StateKeyVals
    block: Block
    post_state: StateKeyVals

def send_message(sock, tag: int, payload: bytes):
    """Send a length-prefixed tagged message over the socket."""
    message = bytes([tag]) + payload
    sock.sendall(struct.pack('<I', len(message)) + message)

def recv_message(sock):
    """Read a length-prefixed tagged message. Returns (tag, payload) or (None, None)."""
    len_bytes = sock.recv(4)
    if len(len_bytes) != 4:
        return None, None
    msg_len = struct.unpack('<I', len_bytes)[0]
    data = b''
    while len(data) < msg_len:
        chunk = sock.recv(msg_len - len(data))
        if not chunk:
            return None, None
        data += chunk
    return data[0], data[1:]

def do_handshake(sock, verbose=False):
    """Perform the fuzzing protocol handshake. Returns True on success."""
    our_peer_info = PeerInfo(
        fuzz_version=U8(1),
        fuzz_features=U32(FEATURE_ANCESTRY | FEATURE_FORK),
        jam_version=Version(major=U8(0), minor=U8(7), patch=U8(2)),
        app_version=Version(major=U8(0), minor=U8(1), patch=U8(0)),
        app_name=String("fuzz.py"),
    )
    send_message(sock, TAG_PEER_INFO, our_peer_info.encode())

    tag, payload = recv_message(sock)
    if tag != TAG_PEER_INFO:
        print(f"Handshake failed: expected TAG_PEER_INFO ({TAG_PEER_INFO}), got {tag}")
        return False

    target_info = PeerInfo.decode(payload)
    print(f"Connected to {target_info.app_name} "
          f"(JAM {target_info.jam_version.major}.{target_info.jam_version.minor}.{target_info.jam_version.patch})")
    if verbose:
        print(f"  fuzz_version={target_info.fuzz_version}, features=0x{int(target_info.fuzz_features):08x}")
    return True

def _load_trace_from_json(path: Path) -> Trace:
    with open(path, "r") as f:
        data = json.load(f)

    def _state_from_json(state_json: dict) -> StateKeyVals:
        return StateKeyVals(
            state_root=Bytes32.from_json(state_json["state_root"]),
            keyvals=TypedVector[KeyVal](
                [
                    KeyVal(
                        key=Bytes[31].from_json(item["key"]),
                        value=Bytes.from_json(item["value"]),
                    )
                    for item in state_json["keyvals"]
                ]
            ),
        )

    return Trace(
        pre_state=_state_from_json(data["pre_state"]),
        block=Block.from_json(data["block"]),
        post_state=_state_from_json(data["post_state"]),
    )

def load_trace(path: Path) -> Trace:
    try:
        return Trace.decode(path.read_bytes())
    except Exception:
        json_path = path.with_suffix(".json")
        if not json_path.exists():
            raise
        return _load_trace_from_json(json_path)

def load_genesis_header(genesis_spec: str) -> Header:
    """Load the genesis header from a dev-spec JSON file."""
    with open(genesis_spec, 'r') as f:
        data = json.load(f)
    return Header.decode(bytes.fromhex(data["genesis_header"]))

def trace_to_initialize(trace: Trace, genesis_header: Header) -> bytes:
    """Build an Initialize payload from the trace pre_state."""
    keyvals = TypedVector[KeyValue]([])
    for kv in trace.pre_state.keyvals:
        keyvals.append(KeyValue(key=Bytes[31](kv.key), value=Bytes(kv.value)))

    init = Initialize(
        header=genesis_header,
        keyvals=State(keyvals=keyvals),
        ancestry=Ancestry(items=TypedVector[AncestryItem]([])),
    )
    return init.encode()


def initialize_trace(sock, trace: Trace, genesis_header: Header, verbose: bool):
    init_payload = trace_to_initialize(trace, genesis_header)
    send_message(sock, TAG_INITIALIZE, init_payload)
    if verbose:
        print(f"  TX: Initialize ({len(init_payload)} bytes)")

    tag, payload = recv_message(sock)
    if tag is None:
        return False, None, "Connection closed after Initialize"
    if tag == TAG_ERROR:
        err = ErrorMessage.decode(payload)
        return False, None, f"Initialize error: {err.message}"
    if tag != TAG_STATE_ROOT:
        return False, None, f"Unexpected tag {tag} after Initialize"

    init_root = payload.hex()
    if verbose:
        print(f"  RX: StateRoot (init) = {init_root}")
    return True, init_root, None

def get_trace_files(trace_dir: Path, module: str, pattern: str):
    """Discover trace .bin files, mirroring test_traces_unified.py logic."""
    if pattern == "all":
        candidates = trace_dir.rglob("*")
        files = [p for p in candidates if p.suffix == '.bin' and p.is_file()]
    else:
        files = []
        for d in trace_dir.glob(module):
            if d.is_dir():
                files.extend(d.glob(pattern))
        files = [p for p in files if p.suffix == '.bin' and p.is_file()]

    files.sort()
    files = [f for f in files if f.name not in ("00000000.bin", "genesis.bin")]
    return files

def fetch_state(sock, header_hash: Bytes32 | bytes, verbose: bool):
    """Send GetState and return a dict of {key_hex: value_hex}."""
    send_message(sock, TAG_GET_STATE, bytes(header_hash))
    if verbose:
        print(f"  TX: GetState ({bytes(header_hash).hex()})")

    tag, payload = recv_message(sock)
    if tag is None:
        print("  Connection closed after GetState")
        return None
    if tag == TAG_ERROR:
        err = ErrorMessage.decode(payload)
        print(f"  GetState error: {err.message}")
        return None
    if tag != TAG_STATE:
        print(f"  Unexpected tag {tag} after GetState")
        return None

    state = State.decode(payload)
    return {bytes(kv.key).hex(): bytes(kv.value).hex() for kv in state.keyvals}

def fetch_state_with_root(sock, header_hash: Bytes32 | bytes, verbose: bool):
    actual_kv = fetch_state(sock, header_hash, verbose)
    if actual_kv is None:
        return None, None

    trie_input = {
        Bytes.fromhex(key_hex): Bytes.fromhex(value_hex)
        for key_hex, value_hex in actual_kv.items()
    }
    actual_root, _ = StateTrie().merkelize(trie_input)
    return actual_kv, actual_root.hex()

def display_state_diff(sock, trace: Trace, header_hash: Bytes32 | bytes, verbose: bool):
    """Fetch actual state from target and diff against expected post_state."""
    actual_kv = fetch_state(sock, header_hash, verbose)
    if actual_kv is None:
        print("  Could not fetch state for diff")
        return

    expected_kv = {bytes(kv.key).hex(): bytes(kv.value).hex() for kv in trace.post_state.keyvals}

    all_keys = sorted(set(actual_kv.keys()) | set(expected_kv.keys()))

    missing = []
    extra = []
    changed = []

    for k in all_keys:
        in_actual = k in actual_kv
        in_expected = k in expected_kv
        if in_expected and not in_actual:
            missing.append(k)
        elif in_actual and not in_expected:
            extra.append(k)
        elif actual_kv[k] != expected_kv[k]:
            changed.append(k)

    print(f"  State diff: {len(changed)} changed, {len(missing)} missing, {len(extra)} extra keys")

    for k in missing:
        print(f"    MISSING key {k}")
        print(f"      expected value: {expected_kv[k][:80]}{'...' if len(expected_kv[k]) > 80 else ''}")

    for k in extra:
        print(f"    EXTRA   key {k}")
        print(f"      actual value:   {actual_kv[k][:80]}{'...' if len(actual_kv[k]) > 80 else ''}")

    for k in changed:
        print(f"    CHANGED key {k}")
        print(f"      expected: {expected_kv[k][:80]}{'...' if len(expected_kv[k]) > 80 else ''}")
        print(f"      actual:   {actual_kv[k][:80]}{'...' if len(actual_kv[k]) > 80 else ''}")

def process_trace(sock, trace: Trace, genesis_header: Header, verbose: bool, do_initialize: bool):
    """
    Run one trace through the protocol: Initialize -> ImportBlock -> check root.
    On root mismatch, fetches full state and displays key-level diff.
    Returns (success: bool, actual_root: str|None, error: str|None).
    """
    expected_root = trace.post_state.state_root.hex()

    if do_initialize:
        ok, init_root, err_msg = initialize_trace(sock, trace, genesis_header, verbose)
        if not ok:
            return False, None, err_msg
    else:
        init_root = None
        if verbose:
            print("  Reusing existing folder session")

    # 2. Import block
    block_payload = trace.block.encode()
    send_message(sock, TAG_IMPORT_BLOCK, block_payload)
    if verbose:
        print(f"  TX: ImportBlock ({len(block_payload)} bytes)")

    tag, payload = recv_message(sock)
    if tag is None:
        return False, None, "Connection closed after ImportBlock"
    if tag == TAG_ERROR:
        err = ErrorMessage.decode(payload)
        actual_kv, actual_root = fetch_state_with_root(sock, trace.block.header.hash(), verbose)
        if actual_root is None:
            return False, None, f"Block error: {err.message} (could not fetch state after rejection)"

        # Block was rejected, so the parent state should still be visible.
        if actual_root == expected_root:
            return True, actual_root, None

        print(f"  Block rejected: {err.message}")
        display_state_diff(sock, trace, trace.block.header.parent, verbose)
        return False, actual_root, f"Block error: {err.message} (actual_root={actual_root}, expected={expected_root})"
    if tag != TAG_STATE_ROOT:
        return False, None, f"Unexpected tag {tag} after ImportBlock"

    actual_root = payload.hex()
    if verbose:
        print(f"  RX: StateRoot (post) = {actual_root}")

    # 3. Compare roots
    if actual_root == expected_root:
        return True, actual_root, None

    # Root mismatch — fetch full state and show diff
    print(f"  Root mismatch: expected={expected_root}, got={actual_root}")
    display_state_diff(sock, trace, trace.block.header.hash(), verbose)
    return False, actual_root, f"Root mismatch: expected={expected_root}, got={actual_root}"

def main():
    parser = argparse.ArgumentParser(
        description='fuzz.py - Replay trace files over the JAM Fuzzing Protocol')
    parser.add_argument('-d', '--trace-dir', required=True,
                        help='Root directory containing trace session folders')
    parser.add_argument('-m', '--module', default='*',
                        help='Module/session directory glob filter (default: *)')
    parser.add_argument('-p', '--pattern', default='*.bin',
                        help='File pattern within module dirs (default: *.bin)')
    parser.add_argument('-s', '--spec', type=str, default='tiny', choices=['tiny', 'full'],
                        help='Specification to use (default: tiny)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--target-sock', default='/tmp/jam_target.sock',
                        help='Target socket path (default: /tmp/jam_target.sock)')
    parser.add_argument('--stop-after', type=int, default=1000,
                        help='Stop after processing this many traces (default: 1000)')
    parser.add_argument('--genesis-spec', default='dev-spec.json',
                        help='Path to dev-spec.json for genesis header (default: dev-spec.json)')

    args = parser.parse_args()
    # set_spec(args.spec)

    trace_dir = Path(args.trace_dir)
    if not trace_dir.exists() or not trace_dir.is_dir():
        print(f"Error: Trace directory '{trace_dir}' does not exist or is not a directory")
        sys.exit(1)

    genesis_header = load_genesis_header(args.genesis_spec)
    print(f"Loaded genesis header from {args.genesis_spec}")

    files = get_trace_files(trace_dir, args.module, args.pattern)
    print(f"Found {len(files)} trace files to process")

    if not files:
        print("No trace files found.")
        sys.exit(0)

    # Connect to target
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(args.target_sock)
        print(f"Connected to target socket: {args.target_sock}")
    except Exception as e:
        print(f"Error connecting to socket '{args.target_sock}': {e}")
        sys.exit(1)

    passed = 0
    failed = 0
    errors = []
    active_folder = None

    try:
        if not do_handshake(sock, args.verbose):
            sys.exit(1)

        for i, path in enumerate(files):
            if i >= args.stop_after:
                print(f"\nStopping after {args.stop_after} traces as requested")
                break

            print(f"\n{'='*70}")
            print(f"[{i+1}/{len(files)}] {path.parent.name}/{path.name}")

            # Load trace
            try:
                trace = load_trace(path)
            except Exception as e:
                print(f"  Error decoding trace: {e}")
                errors.append((path.name, str(e)))
                continue

            folder_changed = path.parent != active_folder
            if folder_changed:
                print("  Session changed: initializing from trace pre_state")
            else:
                print("  Reusing existing folder state")

            # Process through the protocol
            try:
                success, actual_root, err_msg = process_trace(
                    sock, trace, genesis_header, args.verbose, folder_changed
                )
            except Exception as e:
                print(f"  Exception: {e}")
                errors.append((path.name, str(e)))
                continue

            if success:
                print(f"  PASSED (root={actual_root[:16]}...)")
                passed += 1
                active_folder = path.parent
            else:
                print(f"  FAILED: {err_msg}")
                failed += 1
                errors.append((path.name, err_msg))
                active_folder = path.parent

    finally:
        sock.close()

    # Summary
    print(f"\n{'='*70}")
    print(f"PASSED: {passed} | FAILED: {failed} | ERRORS: {len(errors) - failed}")
    print(f"{'='*70}")
    if errors:
        print("\nFailures/Errors:")
        for name, err in errors:
            print(f"  - {name}: {err}")

if __name__ == '__main__':
    main()
