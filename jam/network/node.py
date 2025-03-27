import asyncio
import json
import ssl

from aioquic.asyncio import serve, connect
from aioquic.asyncio.server import QuicServer
from aioquic.quic.configuration import QuicConfiguration
from jam.types.protocol.validators import ValidatorData
from .certificate import generate_keys
from .peer import Peer
from .quic import QuicServerProtocol, QuicClientProtocol
from .sessions import SessionTicketStore
from jam.config.logging import logger

genesis_hash = "476243ad"
protocol_version = "0"

class Node:
    __id: str
    name: str
    host: str
    port: int
    validator_data: ValidatorData
    seed: bytes

    peers: list[Peer]

    dns: str
    server: QuicServer

    is_initialized: bool = False

    connections: list[QuicClientProtocol] = []

    def __init__(self, node_id: str, node_name: str, host: str, port: int, validator_data, peers: list[Peer]):
        self.__id = node_id
        self.name = node_name
        self.host = host
        self.port = port
        self.validator_data = validator_data
        self.peers = peers

        self.dns = generate_keys(port)

    def configuration(self, is_client: bool) -> QuicConfiguration:
        properties = {
            "is_client": is_client,
            "server_name": self.dns
        }
        configuration = QuicConfiguration(**properties)
        configuration.load_cert_chain(f"seeds/{self.port}/cert.pem", f"seeds/{self.port}/key.pem")
        configuration.load_verify_locations(cafile=f"seeds/{self.port}/cert.pem")
        configuration.verify_mode = ssl.CERT_NONE

        if is_client:
            configuration.max_data = 10_000_000  # 10 MB
            configuration.max_stream_data = 1_000_000  # 1 MB per stream

        configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}"]
        return configuration
    
    async def run_server(self):
        session_ticket_store = SessionTicketStore(self.name)

        logger.info(f"🚀 ({self.name}) Listening on {self.host}:{self.port}")

        server = await serve(
            self.host,
            self.port,
            configuration=self.configuration(False),
            create_protocol=QuicServerProtocol,
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
        )

        self.server = server

    async def connect_peer(self, peer: Peer):
        session_ticket_store = SessionTicketStore(self.name)

        # while True:
        try:
            # Skip self
            if peer.host == self.host and peer.port == self.port:
                logger.info(f"⚠️ Skipping self ({self.host}:{self.port})")
                return
            
            logger.info(f"🔹 ({self.name}) Creating new connection to {peer.host}:{peer.port} via QUIC...")
            # Store the client object directly without using context manager
            # so the connection stays open
            async with connect(
                    peer.host,
                    peer.port,
                    configuration=self.configuration(True),
                    create_protocol=QuicClientProtocol,
                    session_ticket_handler=session_ticket_store.add,
            ) as client:
                # client = client
                self.connections.append(client)
                logger.info(f"🤝 ({self.name}) Connection to {peer.host}:{peer.port} established ✅")
                stream_id = client._quic.get_next_available_stream_id()
                client._quic.send_stream_data(stream_id, json.dumps({
                    "type": "ping",
                    "from": self.name
                }).encode())

                self.is_initialized = True

                # Keep the connection alive until it's closed
                # while True:
                #     await asyncio.sleep(10)
                #     client._quic.send_stream_data(stream_id, json.dumps({
                #         "type": "ping",
                #         "from": self.name
                #     }).encode())

                # Wait indefinitely - the connection will be managed by the context manager
                await asyncio.Future()

        except asyncio.CancelledError:
            logger.info(f"🔴 ({self.name}) Connection with {peer.host}:{peer.port} cancelled")
        except Exception as e:
            logger.warning(f"⚠️ ({self.name}) Failed to connect to {peer}: {e}")

    async def run_client(self):
        tasks = []
        for peer in self.peers:
            tasks.append(asyncio.create_task(self.connect_peer(peer)))
        await asyncio.gather(*tasks)

    async def initialize(self):
        logger.info(f"🚀 ({self.name}) Starting server on {self.host}:{self.port}")
        await self.run_server()
        # Give server time to fully initialize
        await asyncio.sleep(1)
        logger.info(f"🔄 ({self.name}) Opening connections to {len(self.peers)} peers...")
        await self.run_client()