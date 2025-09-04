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
from tsrkit_types import Bytes, TypedVector, structure

from .constants import (
    TAG_PEER_INFO,
    TAG_IMPORT_BLOCK,
    TAG_SET_STATE,
    TAG_GET_STATE,
    TAG_STATE,
    TAG_STATE_ROOT,
)


@structure 
class KeyVal:
    key: Bytes[31]
    value: Bytes 

@structure 
class SetStateData:
    header: Header
    state: TypedVector[KeyVal]

SetState = TypedVector[SetStateData]


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

    # For this implementation, we don't decode the fuzzer's PeerInfo
    print("📨 Received PeerInfo from fuzzer. Responding...")

    # Create our PeerInfo response
    # PeerInfo ::= SEQUENCE { name UTF8String, app-version Version, jam-version Version }
    # Version ::= SEQUENCE { major, minor, patch }
    name = b"tessera-node-target"
    name_len = bytes([len(name)])
    # app-version: 1.0.0, jam-version: 2.0.0
    version_payload = name_len + name + b'\x01\x00\x00' + b'\x02\x00\x00'
    
    send_message(conn, TAG_PEER_INFO, version_payload)
    print("✅ Handshake complete.")
    return True


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
                    try:
                        block = Block.decode(payload)
                        if record_enabled and json_data:
                            json_data["blocks"].append(block.to_json())
                        state.transition(block)
                        duration = time.time() - start_time
                        print(f"⚡ Block transition completed in {duration:.4f}s")
                        send_message(conn, TAG_STATE_ROOT, state.root)
                    except Exception as e:
                        print(f"❌ Block processing failed: {e}", file=sys.stderr)
                        # Send empty root on error
                        send_message(conn, TAG_STATE_ROOT, b'\x00' * 32)

                elif tag == TAG_SET_STATE:
                    print(f"🔧 Received SetState command ({len(payload)} bytes)")
                    try:
                        data = SetStateData.decode(payload)
                        if record_enabled and json_data:
                            json_data["pre_state"] = data.state.to_json()
                        
                        from jam.state.state import setup_state
                        state = setup_state(settings.state_db, {keyval.key: keyval.value for keyval in data.state})
                        print(f"✅ State updated. Root: {state.root.hex()}")
                        send_message(conn, TAG_STATE_ROOT, state.root)
                    except Exception as e:
                        print(f"❌ SetState failed: {e}", file=sys.stderr)
                        send_message(conn, TAG_STATE_ROOT, b'\x00' * 32)
                
                elif tag == TAG_GET_STATE:
                    print(f"📤 Received GetState command ({len(payload)} bytes)")
                    print(f"🔍 Current StateRoot: {state.root.hex()}")

                    try:
                        state_vector = TypedVector[KeyVal]([])
                        for key, val in settings.state_db.get_all().items():
                            state_vector.append(KeyVal(Bytes[31](key[:31]), Bytes(val)))

                        if record_enabled and json_data:
                            json_data["post_state"] = state_vector.to_json()
                        
                        send_message(conn, TAG_STATE, state_vector.encode())
                    except Exception as e:
                        print(f"❌ GetState failed: {e}", file=sys.stderr)
                        send_message(conn, TAG_STATE, b'')

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
    settings = setup_setting(db_path, 1, "fuzzer", 40001)

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
