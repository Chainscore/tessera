import asyncio
import ssl

from aioquic.asyncio import serve, connect
from aioquic.asyncio.server import QuicServer
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from jam.config.logging import logger
from jam.config.settings import settings
from jam.consensus.grandpa.finality import Finality
from jam.types.protocol.validators import ValidatorData
from jam.types.protocol.crypto import Hash

from typing import Dict, cast, Tuple, Optional

from .certificate import generate_keys
from .peer import Peer
from .sessions import SessionTicketStore


genesis_hash = "476243ad"
protocol_version = "0"

_original_initialize = QuicConnection._initialize

def _initialize(self, peer_cid: bytes) -> None:
    _original_initialize(self, peer_cid)
    self.tls._request_client_certificate = True

QuicConnection._initialize = _initialize

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
    from .quic.client import QuicClientProtocol

    # Node Data
    __id: str
    dns: str
    name: str
    host: str
    port: int
    seed: bytes
    validator_data: ValidatorData

    # Peers & Connections
    peers: list[Peer]
    peer_map: Dict[Ed25519PublicKey, Peer] = {}
    peer_conn: Dict[Peer, Tuple[int, QuicClientProtocol]] = {}

    # Server
    server: QuicServer

    # Flags
    is_initialized: bool = False
    is_builder: bool = False
    is_validator: bool = True

    connections: list[QuicClientProtocol] = []

    def __init__(self, node_name: str, host: str, port: int, validator_data, peers: list[Peer], is_builder: bool, is_validator: bool):
        self.name = node_name
        self.host = host
        self.port = port
        self.validator_data = validator_data

        # Peers
        self.peers = peers
        self.peer_map = {}
        self.peer_conn = {}
        self.connections = []
        
        self.is_builder = is_builder
        self.is_validator = is_validator
        for peer in self.peers:
            self.peer_map[peer.data.ed25519] = peer

        if is_validator and is_builder:
            raise ValueError("Node can't be validator and builder at same time!")

        self.__id = generate_keys(port)

    def get_peer(self, key: Ed25519PublicKey) -> Peer | None:
        if key in self.peer_map:
            return self.peer_map[key]
        
        return None
    
    def quic_config(self, is_client: bool = True, peer: Optional[Peer] = None) -> QuicConfiguration:
        """
        Utility function to build quic configuration.
        Args:
            is_client (bool): Flag indicating node is a client
            peer (Peer): Peer Information
        Returns:
            config (QuicConfiguration): A QUIC Configuration
        """
        properties = {
            "is_client": is_client,
        }

        config = QuicConfiguration(**properties)
        config.load_cert_chain(f"seeds/{self.port}/cert.pem", f"seeds/{self.port}/key.pem")
        config.verify_mode = ssl.CERT_NONE

        config.max_data = 104857600  # 100 MB
        config.max_stream_data = 10485760  # 10 MB per stream
        config.max_datagram_size = 1350

        if is_client and peer:
            config.server_name = peer.id

        if self.is_builder:
            config.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}/builder"]
        else:
            config.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}", f"jamnp-s/{protocol_version}/{genesis_hash}/builder"]

        return config
    
    async def run_server(self):
        """
        Function to initialize server connection of the node.
        """
        from .quic.server import QuicServerProtocol

        session_ticket_store = SessionTicketStore(self.port)

        logger.info(f"🚀 ({self.name}) Listening on {self.host}:{self.port}")

        # Start server connection
        server = await serve(
            self.host,
            self.port,
            configuration=self.quic_config(is_client=False),
            create_protocol=lambda *args, **kwargs: QuicServerProtocol(*args, node=self, **kwargs),
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
        from .base.quic import QuicProtocol
        from jam.network.protocols.up_0 import Final, Handshake, Leaves

        try:
            # Skip self
            if str(peer.data.metadata.host) == self.host and int(peer.data.metadata.port) == self.port:
                logger.info(f"⚠️ ({self.name}) Skipping self ({self.host}:{self.port})")
                return
            
            logger.info(f"🔹 ({self.name}) Creating new connection to {str(peer.data.metadata.host)}:{int(peer.data.metadata.port)} via QUIC...")

            async with connect(
                    str(peer.data.metadata.host),
                    int(peer.data.metadata.port),
                    configuration=self.configuration(),
                    create_protocol=lambda *args, **kwargs: QuicProtocol(*args, node=self, **kwargs),
                    session_ticket_handler=session_ticket_store.add,
            ) as client:

                # Save peer connection
                client = cast(QuicProtocol, client)

                logger.info(f"🤝 ({self.name}) Connection to {str(peer.data.metadata.host)}:{int(peer.data.metadata.port)} established ✅")

                stream_id = client._quic.get_next_available_stream_id()
                
                db = settings.db
                finality = Finality()

                final_block = finality.load_final(db)

                header_hash  = Hash.blake2b(final_block.header.encode())
                block_slot = final_block.header.slot
                
                final = Final(header_hash=header_hash, time_slot=block_slot)
                leaves = Leaves([])

                handshake = Handshake(final, leaves)

                # Handshake Message
                client.stream_and_keep_open(handshake.encode(), stream_id)

                self.peer_conn[peer] = stream_id, client
                self.is_initialized = True

                # Wait indefinitely - the connection will be managed by the context manager
                await asyncio.Future()

        except asyncio.CancelledError:
            logger.info(f"🔴 ({self.name}) Connection with {str(peer.data.metadata.host)}:{int(peer.data.metadata.port)} cancelled")
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
