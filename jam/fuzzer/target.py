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
import struct
import sys
import shutil
from typing import Optional, Tuple

from jam.block.block import Block
from jam.block.header import Header
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


def read_message(conn: socket.socket) -> Tuple[Optional[int], Optional[bytes]]:
    """
    Reads a length-prefixed message from the connection.
    The fuzzer sends messages with a 4-byte little-endian length prefix.
    
    Returns:
        Tuple of (tag, payload) or (None, None) if connection closed
    """
    try:
        # Read the 4-byte length prefix
        len_bytes = conn.recv(4)
        if not len_bytes:
            return None, None  # Connection closed
        
        msg_len = struct.unpack('<I', len_bytes)[0]
        
        # Read the full message payload
        message = b''
        while len(message) < msg_len:
            chunk = conn.recv(msg_len - len(message))
            if not chunk:
                raise IOError("Socket connection broken while reading message")
            message += chunk
            
        tag = message[0]
        payload = message[1:]
        return tag, payload
    except (IOError, struct.error) as e:
        print(f"Error reading message: {e}", file=sys.stderr)
        return None, None


def send_message(conn: socket.socket, tag: int, payload: bytes) -> None:
    """
    Sends a length-prefixed message to the connection.
    """
    try:
        message = bytes([tag]) + payload
        len_bytes = struct.pack('<I', len(message))
        conn.sendall(len_bytes + message)
    except IOError as e:
        print(f"Error sending message: {e}", file=sys.stderr)


def handle_handshake(conn: socket.socket) -> bool:
    """
    Handles the initial handshake with the fuzzer.
    1. Receives the fuzzer's PeerInfo.
    2. Sends our own PeerInfo in response.
    
    Returns:
        True if handshake successful, False otherwise
    """
    print("🤝 Waiting for fuzzer handshake...")
    tag, payload = read_message(conn)

    if tag is None:
        print("Connection closed before handshake.", file=sys.stderr)
        return False

    if tag != TAG_PEER_INFO:
        print(f"Expected PeerInfo (tag {TAG_PEER_INFO}), but got tag {tag}. Terminating.", file=sys.stderr)
        return False

    # Decode the fuzzer's PeerInfo
    try:
        fuzzer_peer_info = PeerInfo.decode(payload)
        print(f"📨 Received PeerInfo from {fuzzer_peer_info.app_name} (fuzz v{fuzzer_peer_info.fuzz_version})")
        print(f"   Features: {fuzzer_peer_info.fuzz_features}, JAM: {fuzzer_peer_info.jam_version.major}.{fuzzer_peer_info.jam_version.minor}.{fuzzer_peer_info.jam_version.patch}")
    except Exception as e:
        print(f"❌ Failed to decode fuzzer PeerInfo: {e}", file=sys.stderr)
        return False

    # Create our PeerInfo response
    our_peer_info = PeerInfo(
        fuzz_version=U8(1),  # Protocol version 1
        fuzz_features=U32(FEATURE_ANCESTRY | FEATURE_FORK),  # We support ancestry and basic forking
        jam_version=Version(major=U8(0), minor=U8(7), patch=U8(0)),  # JAM 0.7.0
        app_version=Version(major=U8(1), minor=U8(0), patch=U8(0)),  # App 1.0.0
        app_name=String("tessera-target")
    )
    
    try:
        response_payload = our_peer_info.encode()
        send_message(conn, TAG_PEER_INFO, response_payload)
        print("✅ Handshake complete.")
        return True
    except Exception as e:
        print(f"❌ Failed to send PeerInfo response: {e}", file=sys.stderr)
        return False


def run_fuzzer_target_loop(sock: socket.socket, settings, record_path: Optional[str] = None):
    """
    The main server loop that listens for connections and handles messages.
    
    Args:
        sock: Unix socket to listen on
        settings: JAM settings object
        record_path: Optional path to record session data
    """
    
    record_enabled = record_path is not None
    json_data = {"blocks": []} if record_enabled else None

    while True:
        conn, addr = sock.accept()
        with conn:
            print("🔌 Fuzzer connected.")
            
            if not handle_handshake(conn):
                continue

            block_count = 0

            # Initialize state
            from jam.state.state import state as _state 
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
                    
                    start_time = time.time()
                    block = Block.decode(payload)
                    if record_enabled and json_data:
                        json_data["blocks"].append(block.to_json())
                    state.transition(block)
                    duration = time.time() - start_time
                    print(f"⚡ Block transition completed in {duration:.4f}s")
                    send_message(conn, TAG_STATE_ROOT, state.root)
                    # try:
                    # except Exception as e:
                    #     print(f"❌ Block processing failed: {e}", file=sys.stderr)
                    #     # Send Error message for protocol-defined failures
                    #     error_msg = ErrorMessage(message=String(f"Block import failed: {str(e)}"))
                    #     send_message(conn, TAG_ERROR, error_msg.encode())

                elif tag == TAG_INITIALIZE:
                    print(f"🔧 Received Initialize command ({len(payload)} bytes)")
                    try:
                        init_data = Initialize.decode(payload)
                        if record_enabled and json_data:
                            json_data["pre_state"] = init_data.keyvals.to_json()
                        
                        from jam.state.state import setup_state
                        # Convert State to dict for setup_state
                        state_dict = {kv.key: kv.value for kv in init_data.keyvals.keyvals}
                        state = setup_state(settings.state_db, state_dict)
                        print(f"✅ State initialized. Root: {state.root.hex()}")
                        send_message(conn, TAG_STATE_ROOT, state.root)
                    except Exception as e:
                        print(f"❌ Initialize failed: {e}", file=sys.stderr)
                        error_msg = ErrorMessage(message=String(f"Initialize failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())
                
                elif tag == TAG_GET_STATE:
                    print(f"📤 Received GetState command ({len(payload)} bytes)")
                    print(f"🔍 Current StateRoot: {state.root.hex()}")

                    try:
                        keyvals = TypedVector[KeyValue]([])
                        for key, val in settings.state_db.get_all().items():
                            # Ensure key is 31 bytes
                            key_31 = key[:31].ljust(31, b'\x00') if len(key) < 31 else key[:31]
                            keyvals.append(KeyValue(key=Bytes[31](key_31), value=Bytes(val)))

                        state_response = State(keyvals=keyvals)
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
    
    from jam.settings import setup_setting
    from jam.log_setup import setup_logging
    settings = setup_setting(db_path, 1, "fuzzer", 40001)
    setup_logging("default", "fuzzer-target")

    # Ensure the socket does not already exist
    if os.path.exists(socket_path):
        os.remove(socket_path)

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    try:
        sock.bind(socket_path)
        sock.listen(1)
        print(f"🛰️  Tessera JAM Fuzzer Target | Listening on {sock.getsockname()}")
        run_fuzzer_target_loop(sock, settings, record_path)
    except KeyboardInterrupt:
        print("\n🛑 Fuzzer target stopped by user")
    except Exception as e:
        print(f"❌ Fuzzer target error: {e}", file=sys.stderr)
        raise
    finally:
        sock.close()
        if os.path.exists(socket_path):
            os.remove(socket_path)
        print("🧹 Cleanup complete.")
