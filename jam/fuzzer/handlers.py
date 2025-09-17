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
        return fuzzer_peer_info
    except Exception as e:
        print(f"❌ Failed to send PeerInfo response: {e}", file=sys.stderr)
        return False

