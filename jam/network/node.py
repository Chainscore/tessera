import asyncio
import json
import ssl
from typing import Dict, cast, Tuple

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
    """
    Represents a node in the network.
    Args:
        node_id (str): Id of the node
        node_name (str): Name of the node
        host (str): Host address
        port (int): Running port of the node
        validator_data (ValidatorData): Public keys and metadata of the node
        peers (list[Peer]): List of all the peers of the node.
    """
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
    is_builder: bool = False

    # state: State

    peer_conn: Dict[Peer, Tuple[int, QuicClientProtocol]] = {}
    connections: list[QuicClientProtocol] = []

    def __init__(self, node_id: str, node_name: str, host: str, port: int, validator_data, peers: list[Peer], is_builder: bool):
        self.__id = node_id
        self.name = node_name
        self.host = host
        self.port = port
        self.validator_data = validator_data
        self.peers = peers
        self.is_builder = is_builder

        self.dns = generate_keys(port)

    def configuration(self, is_client: bool = True) -> QuicConfiguration:
        """
        Utility function to build quic configuration.
        Args:
            is_client (bool): Flag indicating node is a client
        Returns:
            config (QuicConfiguration): A QUIC Configuration
        """
        properties = {
            "is_client": is_client,
        }

        configuration = QuicConfiguration(**properties)
        configuration.load_cert_chain(f"seeds/{self.port}/cert.pem", f"seeds/{self.port}/key.pem")
        configuration.load_verify_locations(cafile=f"seeds/{self.port}/cert.pem")
        configuration.verify_mode = ssl.CERT_NONE

        configuration.max_data = 104857600  # 100 MB
        configuration.max_stream_data = 10485760  # 10 MB per stream
        configuration.max_datagram_size = 1350

        if is_client:
            configuration.server_name = self.dns

        if self.is_builder:
            configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}/builder"]
        else:
            configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}", f"jamnp-s/{protocol_version}/{genesis_hash}/builder"]

        return configuration
    
    async def run_server(self):
        """
        Function to initialize server connection of the node.
        """
        session_ticket_store = SessionTicketStore(self.port)

        logger.info(f"🚀 ({self.name}) Listening on {self.host}:{self.port}")

        server = await serve(
            self.host,
            self.port,
            configuration=self.configuration(is_client=False),
            create_protocol=QuicServerProtocol,
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
        )

        # Save server connection
        self.server = server

    async def connect_peer(self, peer: Peer):
        """
        Function to connect the node to a peer.
        """
        session_ticket_store = SessionTicketStore(self.port)

        try:
            # Skip self
            if peer.host == self.host and peer.port == self.port:
                logger.info(f"⚠️ Skipping self ({self.host}:{self.port})")
                return
            
            logger.info(f"🔹 ({self.name}) Creating new connection to {peer.host}:{peer.port} via QUIC...")

            async with connect(
                    peer.host,
                    peer.port,
                    configuration=self.configuration(),
                    create_protocol=QuicClientProtocol,
                    session_ticket_handler=session_ticket_store.add,
            ) as client:

                # Save peer connection
                self.connections.append(client)
                client = cast(QuicClientProtocol, client)

                logger.info(f"🤝 ({self.name}) Connection to {peer.host}:{peer.port} established ✅")

                stream_id = client._quic.get_next_available_stream_id()
                client.stream_and_keep_open(stream_id=stream_id,message=json.dumps({
                    "type": "ping",
                    "from": self.name
            }).encode())

                # last_block = self.state.beta[-1]
                # final = Final(block_hash=last_block.header_hash, time_slot=U32(0))
                # await client.stream_and_keep_open(stream_id=stream_id, message=final.encode())

                self.peer_conn[peer] = stream_id, client


                self.is_initialized = True

                # Wait indefinitely - the connection will be managed by the context manager
                await asyncio.Future()

        except asyncio.CancelledError:
            logger.info(f"🔴 ({self.name}) Connection with {peer.host}:{peer.port} cancelled")
        except Exception as e:
            logger.warning(f"⚠️ ({self.name}) Failed to connect to {peer}: {e}")

    async def run_client(self):
        """
        Function to initialize client connections of the node.
        """
        tasks = []
        for peer in self.peers:
            tasks.append(asyncio.create_task(self.connect_peer(peer)))
        await asyncio.gather(*tasks)

    async def initialize(self):
        """
        Function to fully initialize a node.
        """
        if self.is_builder:
            logger.info(f"🚀 ({self.name}) Starting builder on {self.host}:{self.port}")

        if not self.is_builder:
            logger.info(f"🚀 ({self.name}) Starting server on {self.host}:{self.port}")
            await self.run_server()

            # Give server time to fully initialize
            await asyncio.sleep(1)

        logger.info(f"🔄 ({self.name}) Opening connections to {len(self.peers)} peers...")
        await self.run_client()
