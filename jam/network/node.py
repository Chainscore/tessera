import asyncio
import json
import ssl

from aioquic.asyncio import serve, connect
from aioquic.asyncio.server import QuicServer
from aioquic.quic.configuration import QuicConfiguration
from .certificate import generate_keys
from .peer import Peer
from .quic import QuicServerProtocol, QuicClientProtocol
from .sessions import SessionTicketStore
from jam.config.logging import logger

class Node:
    __id: str
    name: str
    host: str
    port: int

    seed: bytes

    peers: list[Peer]

    dns: str
    server: QuicServer

    is_initialized: bool = False

    connections: list[QuicClientProtocol] = []

    def __init__(self, node_id: str, node_name: str, host: str, port: int, peers: list[Peer]):
        self.__id = node_id
        self.name = node_name
        self.host = host
        self.port = port
        self.peers = peers

        self.dns = generate_keys(port)

    async def run_server(self):
        session_ticket_store = SessionTicketStore(self.name)

        configuration = QuicConfiguration(is_client=False)
        configuration.load_cert_chain(f"seeds/{self.port}/cert.pem", f"seeds/{self.port}/key.pem")
        configuration.load_verify_locations(cafile=f"seeds/{self.port}/cert.pem")
        configuration.verify_mode = ssl.CERT_NONE

        genesis_hash = "476243ad"
        protocol_version = "0"
        configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}"]

        logger.info(f"🚀 ({self.name}) Listening on {self.host}:{self.port}")

        server = await serve(
            self.host,
            self.port,
            configuration=configuration,
            create_protocol=QuicServerProtocol,
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
        )

        self.server = server
        # await asyncio.Future()

    async def connect_peer(self, peer: Peer, configuration: QuicConfiguration):
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
                    configuration=configuration,
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

                # Keep the connection alive until it's closed
                # ping_task = asyncio.create_task(self._send_periodic_pings(peer, client))

                self.is_initialized = True

                # Wait indefinitely - the connection will be managed by the context manager
                await asyncio.Future()

        except asyncio.CancelledError:
            logger.info(f"🔴 ({self.name}) Connection with {peer.host}:{peer.port} cancelled")
        except Exception as e:
            logger.warning(f"⚠️ ({self.name}) Failed to connect to {peer}: {e}")

    async def run_client(self):

        tasks = []

        for peer in self.peers:
            if peer.host == self.host and peer.port == self.port:
                # verify san
                logger.info(f"San verification for {self.name}: {self.dns == peer.san}")
                logger.info(f"⚠️ Skipping self ({self.host}:{self.port})")
                continue
            configuration = QuicConfiguration(is_client=True, server_name=self.dns)
            configuration.load_cert_chain(f"seeds/{self.port}/cert.pem", f"seeds/{self.port}/key.pem")
            configuration.load_verify_locations(cafile=f"seeds/{self.port}/cert.pem")
            configuration.verify_mode = ssl.CERT_NONE

            genesis_hash = "476243ad"
            protocol_version = "0"
            configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}"]

            tasks.append(asyncio.create_task(self.connect_peer(peer, configuration)))
            # await self.connect_peer(peer, configuration)

        await asyncio.gather(*tasks)

    async def initialize(self):
        logger.info(f"🚀 ({self.name}) Starting server on {self.host}:{self.port}")
        await self.run_server()
        # Give server time to fully initialize
        await asyncio.sleep(1)
        logger.info(f"🔄 ({self.name}) Opening connections to {len(self.peers)} peers...")
        await self.run_client()