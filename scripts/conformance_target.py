import json
# from jam.block.header import Header
from tsrkit_types import Bytes, TypedVector, structure
import socket
import time
import os
import struct
import argparse
import sys
from jam.state.state import State, setup_state
import shutil

from jam.types.block.block import Block
from jam.types.block.header import Header

# ASN.1 Tags for the JAM Fuzzing Protocol
TAG_PEER_INFO = 0
TAG_IMPORT_BLOCK = 1
TAG_SET_STATE = 2
TAG_GET_STATE = 3
TAG_STATE = 4
TAG_STATE_ROOT = 5


@structure
class KeyVal:
    key: Bytes[31]
    value: Bytes

@structure
class SetStateData:
    header: Header
    state: TypedVector[KeyVal]

SetState = TypedVector[SetStateData]

def read_message(conn):
    """
    Reads a length-prefixed message from the connection.
    The fuzzer sends messages with a 4-byte little-endian length prefix.
    """
    try:
        # Read the 4-byte length prefix
        len_bytes = conn.recv(4)
        if not len_bytes:
            return None, None # Connection closed

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

def send_message(conn, tag, payload):
    """
    Sends a length-prefixed message to the connection.
    """
    try:
        message = bytes([tag]) + payload
        len_bytes = struct.pack('<I', len(message))
        conn.sendall(len_bytes + message)
    except IOError as e:
        print(f"Error sending message: {e}", file=sys.stderr)


def handle_handshake(conn):
    """
    Handles the initial handshake with the fuzzer.
    1. Receives the fuzzer's PeerInfo.
    2. Sends our own PeerInfo in response.
    """
    print("Waiting for fuzzer handshake...")
    tag, payload = read_message(conn)

    if tag is None:
        print("Connection closed before handshake.", file=sys.stderr)
        return False

    if tag != TAG_PEER_INFO:
        print(f"Expected PeerInfo (tag {TAG_PEER_INFO}), but got tag {tag}. Terminating.", file=sys.stderr)
        return False

    # For this demo, we don't bother decoding the fuzzer's PeerInfo
    print("Received PeerInfo from fuzzer. Responding...")

    # --- Create our PeerInfo response ---
    # A minimal, hardcoded PeerInfo message.
    # PeerInfo ::= SEQUENCE { name UTF8String, app-version Version, jam-version Version }
    # Version ::= SEQUENCE { major, minor, patch }
    name = b"python-demo-target"
    name_len = bytes([len(name)])
    # app-version: 1.0.0, jam-version: 2.0.0
    version_payload = name_len + name + b'\x01\x00\x00' + b'\x02\x00\x00'

    send_message(conn, TAG_PEER_INFO, version_payload)
    print("Handshake complete.")
    return True

def main_loop(sock, settings):
    """
    The main server loop that listens for connections and handles messages.
    """
    print(f"Python JAM Target listening on {sock.getsockname()}")
    RECORD = True

    json_data = {}
    json_data["blocks"] = []
    while True:
        conn, addr = sock.accept()
        with conn:
            print(f"Fuzzer connected.")

            if not handle_handshake(conn):
                continue

            block_count = 0

            from jam.state.state import state as _state
            state = _state

            while True:
                tag, payload = read_message(conn)

                if tag is None:
                    if RECORD:
                        with open("record.json", "w") as json_record:
                            json.dump(json_data, json_record, indent=4)
                    print("Fuzzer closed connection.")
                    break

                if tag == TAG_IMPORT_BLOCK:
                    block_count += 1
                    print(f"<- Received Block #{block_count} ({len(payload)} bytes)")
                    json_data["blocks"].append(payload.hex())
                    start_time = time.time()
                    block = Block.decode(payload)
                    state.transition(block)
                    print(f"-- Transition took {time.time() - start_time}s --")
                    send_message(conn, TAG_STATE_ROOT, state.root)

                elif tag == TAG_SET_STATE:
                    print(f"<- Received SetState command ({len(payload)} bytes)")
                    data = SetStateData.decode(payload)
                    json_data["pre_state"] = data.state.to_json()
                    print("previous data",settings.state_db)
                    state = setup_state(settings.state_db, {keyval.key:keyval.value for keyval in data.state})
                    print(f"-> Sending StateRoot", state.root.hex())
                    send_message(conn, TAG_STATE_ROOT, state.root)

                elif tag == TAG_GET_STATE:
                    print(f"<- Received GetState command ({len(payload)} bytes)", payload.hex())
                    print(f"-> Sending StateRoot", state.root.hex())

                    state = TypedVector[KeyVal]([])
                    for key, val in settings.state_db.get_all().items():
                        state.append(KeyVal(Bytes[31](key[:31]), Bytes(val)))

                    json_data["post_state"] = state.to_json()
                    send_message(conn, TAG_STATE, state.encode())

                else:
                    print(f"Received unexpected message with tag {tag}. Closing connection.", file=sys.stderr)
                    break

def main():
    parser = argparse.ArgumentParser(description="Python Demo JAM Target for conformance testing.")
    parser.add_argument("-s", "--socket", default="/tmp/jam_conformance.sock",
                        help="Unix socket path to listen on.")
    args = parser.parse_args()

    from jam.config.settings import setup_setting

    shutil.rmtree("data/tmp", ignore_errors=True)
    settings = setup_setting("data/tmp/", 1, "prasad", 40001)

    socket_path = args.socket

    # Ensure the socket does not already exist
    if os.path.exists(socket_path):
        os.remove(socket_path)

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        sock.bind(socket_path)
        sock.listen(1)
        main_loop(sock, settings)
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        sock.close()
        if os.path.exists(socket_path):
            os.remove(socket_path)
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
