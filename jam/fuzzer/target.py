"""
JAM Conformance Testing Fuzzer Target

This module implements a fuzzer target that follows the JAM Fuzzing Protocol
for conformance testing. It handles handshakes and processes various message
types including block imports, state operations, and root queries.
"""
import json
import socket
import os
import sys
import shutil
import structlog
from typing import Optional

from jam.block.block import Block
from tsrkit_types import Bytes, Bytes32, U8, U32, TypedVector, String, structure

from .constants import (
    TAG_PEER_INFO,
    TAG_INITIALIZE,
    TAG_IMPORT_BLOCK,
    TAG_GET_STATE,
    TAG_STATE,
    TAG_STATE_ROOT,
    TAG_ERROR,
    FEATURE_ANCESTRY,
    FEATURE_FORK,
)
from .types import PeerInfo, Version, Initialize, State as FuzzerState, KeyValue, ErrorMessage

from .handlers import read_message, send_message, handle_handshake
from ..block.extrinsics.extrinsic import Extrinsic


class _NoOpPublisher:
    """Stub publisher for fuzzer — all publish calls are silent no-ops."""
    async def publish_statistics(self, *a, **kw): pass
    async def publish_best_block(self, *a, **kw): pass
    async def publish_finalized_block(self, *a, **kw): pass


class _NoOpResponder:
    """Stub RPC responder that only exposes a no-op publisher."""
    def __init__(self):
        self.publisher = _NoOpPublisher()


class FuzzerNode:
    """
    Lightweight JamNode-compatible shim for conformance testing.

    Provides the minimal interface that State, FinalityService, and BlockView
    depend on, without bringing in networking, operator, or full RPC services.
    """

    def __init__(self, db_path: str, seed: int = 1, port: int = 40001):
        from jam.config import NodeConfig
        from jam.settings import Settings
        from jam.block.extrinsics.pool import ExtrinsicPool

        config = NodeConfig(
            DATA_PATH=db_path,
            SEED=str(seed),
            NODE_NAME="fuzzer",
            PORT=port,
            RPC_FLAG=False,
        )

        self._settings = Settings(config)
        self._state = None
        self._pool = ExtrinsicPool()
        self._responder = _NoOpResponder()
        self.logger = structlog.get_logger("fuzzer")

        # Deferred — set after settings are ready
        self._ledger = None
        self._grandpa = None

    def _init_services(self):
        """Initialize BlockView and FinalityService (requires settings to be ready)."""
        from jam.block.block_view import BlockView
        from jam.finality.service import FinalityService

        self._ledger = BlockView(self)
        self._grandpa = FinalityService(self)
        self._ledger.initialize()

    @property
    def settings(self):
        return self._settings

    @property
    def state(self):
        if self._state is None:
            raise RuntimeError("Fuzzer state not initialized yet")
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def ledger(self):
        if self._ledger is None:
            raise RuntimeError("BlockView not initialized yet")
        return self._ledger

    @property
    def grandpa(self):
        if self._grandpa is None:
            raise RuntimeError("FinalityService not initialized yet")
        return self._grandpa

    @property
    def pool(self):
        return self._pool

    @property
    def responder(self):
        return self._responder

    def reset(self):
        """Clear all databases and reset services for a new trace session."""
        # Clear state DB
        for key in self.settings.state_db.get_all():
            self.settings.state_db.delete(key)

        # Clear main DB
        for key in self.settings.main_db.get_all():
            self.settings.main_db.delete(key)

        # Re-initialize services with clean DBs
        self._state = None
        self._init_services()


def run_fuzzer_target_loop(sock: socket.socket, db_path: str, record_path: Optional[str] = None):
    """
    The main server loop that listens for connections and handles messages.

    Args:
        sock: Unix socket to listen on
        db_path: DB path
        record_path: Optional path to record session data
    """

    record_enabled = record_path is not None
    json_data = {"blocks": []} if record_enabled else None
    SESSION_ID = 0
    record_index = 0

    while True:
        print("V0.7.2")
        conn, addr = sock.accept()
        with conn:
            print("🔌 Fuzzer connected.")

            peer = handle_handshake(conn)
            if not peer:
                continue
            else:
                print(">> Connected to", peer.to_json())
                try:
                    db_ = db_path + str(SESSION_ID)
                    node = FuzzerNode(db_, seed=1, port=40001)
                except Exception as e:
                    SESSION_ID += 1
                    db_ = db_path + str(SESSION_ID)
                    node = FuzzerNode(db_, seed=1, port=40001)

            node._init_services()
            block_count = 0

            while True:
                tag, payload = read_message(conn)

                if tag is None:
                    if record_enabled and json_data:
                        with open(record_path, "w") as json_record:
                            json.dump(json_data, json_record, indent=4)
                        print(f"📝 Session data recorded to {record_path}")
                    print("🔌 Fuzzer closed connection.")
                    break

                if tag == TAG_IMPORT_BLOCK:
                    block_count += 1
                    print(f"📦 Received Block #{block_count} ({len(payload)} bytes)")

                    try:
                        block = Block.decode(payload)

                        if record_enabled and json_data:
                            json_data["blocks"].append(block.to_json())

                        valid_block = node.state._force_transition(block, True, True)
                        if valid_block:
                            from jam.state.state import State
                            post_state = State.load(node, block.header.hash())
                            send_message(conn, TAG_STATE_ROOT, post_state.root)

                            record_index += 1
                        else:
                            send_message(conn, TAG_ERROR, String("Invalid block. Error message unavailable").encode())
                    except Exception as e:
                        print(f"❌ Block processing failed: {e}", file=sys.stderr)
                        error_msg = ErrorMessage(message=String(f"Block import failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())

                elif tag == TAG_INITIALIZE:
                    print(f"🔧 Received Initialize command ({len(payload)} bytes)")
                    try:
                        init_data = Initialize.decode(payload)
                        if record_enabled and json_data:
                            json_data["pre_state"] = init_data.keyvals.to_json()

                        # Reset all databases and services for this new trace
                        node.reset()

                        # Convert keyvals to dict for State.from_keyvals
                        from jam.state.state import State
                        state_dict = {kv.key: kv.value for kv in init_data.keyvals.keyvals}
                        node.state = State.from_keyvals(state_dict, node)
                        node.state.store.enable_writes()
                        node.state.store.enable_cache()

                        print(f"✅ State initialized. Root: {node.state.root.hex()}")

                        # Finalize initial block
                        block = Block(init_data.header, Extrinsic.empty())
                        hh = block.save(node.settings.main_db)
                        node.grandpa.set_head(block)
                        node.state.stash(hh)
                        node.grandpa.finalise(block)
                        node.state.settle(hh)

                        send_message(conn, TAG_STATE_ROOT, node.state.root)
                    except Exception as e:
                        print(f"❌ Initialize failed: {e}", file=sys.stderr)
                        error_msg = ErrorMessage(message=String(f"Initialize failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())

                elif tag == TAG_GET_STATE:
                    print(f"📤 Received GetState command ({len(payload)} bytes)")
                    print(f"🔍 Current StateRoot: {node.state.root.hex()}")

                    try:
                        keyvals = TypedVector[KeyValue]([])
                        for key, val in node.settings.state_db.get_all().items():
                            # Ensure key is 31 bytes
                            key_31 = key[:31].ljust(31, b'\x00') if len(key) < 31 else key[:31]
                            keyvals.append(KeyValue(key=Bytes[31](key_31), value=Bytes(val)))

                        state_response = keyvals
                        if record_enabled and json_data:
                            json_data["post_state"] = state_response.to_json()

                        send_message(conn, TAG_STATE, state_response.encode())
                    except Exception as e:
                        print(f"❌ GetState failed: {e}", file=sys.stderr)
                        error_msg = ErrorMessage(message=String(f"GetState failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())

                else:
                    print(f"❓ Received unexpected message with tag {tag}. Closing connection.", file=sys.stderr)
                    break

                print("\n---------\n")

async def run_fuzzer_target(
    db_path: str,
    socket_path: str = "/tmp/jam_conformance.sock",
    record_path: Optional[str] = "fuzzer_session.json"
) -> None:
    """
    Run the JAM fuzzer target server.

    Args:
        db_path: Path to database directory
        socket_path: Unix socket path to listen on
        record_path: Optional path to record session data
    """

    # Clean up and setup database
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    from jam.log_setup import setup_logging
    setup_logging("default", "fuzzer-target")

    # Ensure the socket does not already exist
    if os.path.exists(socket_path):
        os.remove(socket_path)

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    if not db_path.endswith("/"):
        db_path = db_path + "/"

    try:
        sock.bind(socket_path)
        sock.listen(1)
        print(f"🛰️  Tessera JAM Fuzzer Target | Listening on {sock.getsockname()}")
        run_fuzzer_target_loop(sock, db_path, record_path)
    except KeyboardInterrupt:
        print("\n🛑 Fuzzer target stopped by user")
    except Exception as e:
        print(f"❌ Fuzzer target error: {e}", file=sys.stderr)
        raise
    finally:
        sock.close()
        if os.path.exists(socket_path):
            os.remove(socket_path)
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        print("🧹 Cleanup complete.")
