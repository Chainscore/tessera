import ssl
import json
import asyncio
import os

from typing import cast, Dict, Tuple
from aioquic.asyncio import connect

from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.logger import QuicFileLogger

from jam.config.logging import setup_logging
from jam.network.quic import QuicClientProtocol
from jam.network.certificate import generate_keys

genesis_hash = "476243ad"
protocol_version = "0"

def configuration(port: int, is_client: bool = True) -> QuicConfiguration:
    """
    Utility function to build quic configuration.
    Args:
        port (int): Port
        is_client (bool): Flag indicating node is a client
    Returns:
        config (QuicConfiguration): A QUIC Configuration
    """
    properties = {
        "is_client": is_client,
    }
    dns = generate_keys(port)
    configuration = QuicConfiguration(**properties)
    configuration.load_cert_chain(f"seeds/{port}/cert.pem", f"seeds/{port}/key.pem")
    configuration.load_verify_locations(cafile=f"seeds/{port}/cert.pem")
    configuration.verify_mode = ssl.CERT_NONE

    configuration.max_data = 1048576 * 50  # 50 MB
    configuration.max_stream_data = 1048576 * 5  # 5 MB per stream
    configuration.max_datagram_size = 1350

    if is_client:
        configuration.server_name = dns

    configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}",
                                    f"jamnp-s/{protocol_version}/{genesis_hash}/builder"]

    log_path = f"logs/qlogs/{port}"
    os.makedirs(log_path, exist_ok=True)
    configuration.quic_logger = QuicFileLogger(path=log_path)

    return configuration

class Peer:
    host: str
    port: int

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

connections: list[QuicClientProtocol] = []
peer_conn: Dict[Peer, Tuple[int, QuicClientProtocol]] = {}

async def connect_peer(host: str, port: int, peer: Peer):
    """
    Function to connect the node to a peer.
    """

    try:
        # Skip self
        if peer.host == host and peer.port == port:
            print(f"⚠️ Skipping self ({host}:{port})")
            return

        print(f"🔹 ({port}) Creating new connection to {peer.host}:{peer.port} via QUIC...")

        async with connect(
                peer.host,
                peer.port,
                configuration=configuration(port=port),
                create_protocol=QuicClientProtocol,
        ) as client:

            # Save peer connection
            connections.append(client)
            client = cast(QuicClientProtocol, client)

            print(f"🤝 ({port}) Connection to {peer.host}:{peer.port} established ✅")

            stream_id = client._quic.get_next_available_stream_id()

            print("Sending Ping")
            client.stream_and_close(stream_id=stream_id, message=json.dumps({
                "type": "ping",
                "from": port
            }).encode())

            peer_conn[peer] = stream_id, client

            await asyncio.Future()

    except asyncio.CancelledError:
        print(f"🔴 ({port}) Connection with {peer.host}:{peer.port} cancelled")
    except Exception as e:
        print(f"⚠️ ({port}) Failed to connect to {peer}: {e}")

async def main() -> None:
    from jam.network.playground.client import run_client
    from jam.network.playground.server import run_server

    setup_logging()

    try:
        print("Starting playground")


        peers: list[Peer] = [Peer(host="127.0.0.1", port=30333)]

        async with asyncio.TaskGroup() as tg:

            async def initialize():
                server = await run_server(port=30333, host="127.0.0.1")
                await asyncio.sleep(2)
                await run_client(port=30334, host="127.0.0.1", peers=peers)

            tg.create_task(initialize())

            async def process(conns: list[QuicClientProtocol]):
                await asyncio.sleep(4)

                message = "A" * 104857600  # 1MB of 'A' characters
                messageb = "B" * 104857600  # 1MB of 'B' characters
                print(f"Message length: {len(message)} bytes")

                for client in conns:
                    print("sending", client)
                    stream_id = client.stream_and_keep_open(message=message.encode())
                    print("Sending and closing")
                    client.stream_and_close(message=messageb.encode(), stream_id=stream_id)
                    print(f"closed stream {stream_id}")

            tg.create_task(process(connections))


    except KeyboardInterrupt:
        print("Shutting down JAM node")
    except Exception as e:
        print(f"Fatal error {str(e)}")
        raise
