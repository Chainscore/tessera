"""
JAM Conformance Testing Fuzzer Target

This module implements a fuzzer target that follows the JAM Fuzzing Protocol
for conformance testing. It handles handshakes and processes various message
types including block imports, state operations, and root queries.
"""
import json
import socket
import time
import os
from pathlib import Path
import sys
import shutil
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
from .types import PeerInfo, Version, Initialize, State, KeyValue, ErrorMessage

from .handlers import read_message, send_message, handle_handshake
from ..block.extrinsics.extrinsic import Extrinsic
from ..types import HeaderHash


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
                from jam.settings import setup_setting
                print(">> Connected to", peer.to_json())
                try:
                    db_ = db_path + str(SESSION_ID)
                    settings = setup_setting(db_, 1, "fuzzer", 40001)
                except Exception as e:
                    SESSION_ID += 1
                    db_ = db_path + str(SESSION_ID)
                    settings = setup_setting(db_, 1, "fuzzer", 40001)


            block_count = 0

            # Initialize state
            from jam.state.state import state as _state, State
            state = _state

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

                        from jam.block.block_view import viewer
                        viewer.record_block(block, settings.main_db)

                        if record_enabled and json_data:
                            json_data["blocks"].append(block.to_json())
                        valid_block = State._force_transition(block, False, True)
                        if valid_block:
                            post_state = State.load(block.header.hash())
                            send_message(conn, TAG_STATE_ROOT, post_state.root)

                            record_index += 1
                        else:
                            send_message(conn, TAG_ERROR, String("Invalid block. Error message unavailable").encode())
                    except Exception as e:
                        print(f"❌ Block processing failed: {e}", file=sys.stderr)
                        # Send Error message for protocol-defined failures
                        error_msg = ErrorMessage(message=String(f"Block import failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())

                elif tag == TAG_INITIALIZE:
                    print(f"🔧 Received Initialize command ({len(payload)} bytes)")
                    try:
                        init_data = Initialize.decode(payload)
                        if record_enabled and json_data:
                            json_data["pre_state"] = init_data.keyvals.to_json()
                        
                        from jam.state.state import setup_state

                        # Clear ALL databases to avoid stale data from previous traces
                        # 1. Clear state DB (stale KV pairs)
                        for key in settings.state_db.get_all():
                            settings.state_db.delete(key)

                        # 2. Clear main DB (stale blocks, finality keys, StateRecords)
                        for key in settings.main_db.get_all():
                            settings.main_db.delete(key)

                        # 3. Reset BlockView singleton to clear in-memory block tree
                        from jam.block.block_view import viewer
                        viewer.initialize(settings.main_db)

                        # Convert State to dict for setup_state
                        state_dict = {kv.key: kv.value for kv in init_data.keyvals.keyvals}
                        state = setup_state(settings.state_db, state_dict)
                        print(f"✅ State initialized. Root: {state.root.hex()}")

                        # Finalize initial block
                        from jam.finality.finality import Finality
                        block = Block(init_data.header, Extrinsic.empty())
                        hh = block.save(settings.main_db)
                        Finality.set_head(block, settings.main_db)
                        Finality.finalise(block, settings.main_db)

                        send_message(conn, TAG_STATE_ROOT, state.root)
                    except Exception as e:
                        print(f"❌ Initialize failed: {e}", file=sys.stderr)
                        error_msg = ErrorMessage(message=String(f"Initialize failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())
                
                elif tag == TAG_GET_STATE:
                    print(f"📤 Received GetState command ({len(payload)} bytes)")
                    print(f"📤 Received GetState payload: {payload.hex()}")
                    print(f"🔍 Current StateRoot: {state.root.hex()}")

                    try:
                        keyvals = TypedVector[KeyValue]([])
                        header_hash = HeaderHash(payload)
                        from jam.block.block_view import viewer, BlockStatus
                        if header_hash is not None:
                            block = viewer.load_ghost(header_hash)
                            if block.status == BlockStatus.audited:
                                st = State.load(block.header)
                                for key, val in st.transform().items():
                                    # Ensure key is 31 bytes
                                    key_31 = key[:31].ljust(31, b'\x00') if len(key) < 31 else key[:31]
                                    keyvals.append(KeyValue(key=Bytes[31](key_31), value=Bytes(val)))
                            elif block.status == BlockStatus.unaudited:
                                st = State.load(block.parent.header)
                                for key, val in st.transform().items():
                                    # Ensure key is 31 bytes
                                    key_31 = key[:31].ljust(31, b'\x00') if len(key) < 31 else key[:31]
                                    keyvals.append(KeyValue(key=Bytes[31](key_31), value=Bytes(val)))

                        # state_response = State(keyvals=keyvals)
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
