import asyncio
import ssl

from aioquic.asyncio import serve, connect
from aioquic.asyncio.server import QuicServer
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.config.logging import get_logger

from jam.types.protocol.validators import ValidatorData
from jam.types.protocol.crypto import Ed25519Public

from typing import Dict, cast, Tuple, Optional

from .base.quic import QuicProtocol
from jam.network.base.certificate import generate_keys
from jam.network.base.protocol import PrefixType
from .peer import Peer
from jam.network.base.sessions import SessionTicketStore


# Module-specific logger
logger = get_logger("network")

genesis_hash = "b5af8eda"
protocol_version = "0"
node_alpn = f"jamnp-s/{protocol_version}/{genesis_hash}"
builder_alpn = node_alpn + "/builder"

_original_initialize = QuicConnection._initialize

def _initialize(self, peer_cid: bytes) -> None:
    _original_initialize(self, peer_cid)
    self.tls._request_client_certificate = True

QuicConnection._initialize = _initialize
INIT_DELAY = 6

class Node:
    """
    Represents a node in the network.
    Args:
        node_name (str): Name of the node
        host (str): Host address
        port (int): Running port of the node
        validator_data (ValidatorData): Public keys and metadata of the node
        peers (list[Peer]): List of all the peers of the node.
    """

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
    peer_map: Dict[bytes, Peer] = {}
    peer_conn: Dict[Peer, Tuple[int, QuicProtocol]] = {}

    # Server
    server: QuicServer

    # Flags
    is_initialized: bool = False
    is_builder: bool = False
    is_validator: bool = True

    def __init__(self, node_name: str, host: str, port: int, validator_data, peers: list[Peer], is_builder: bool, is_validator: bool):
        self.name = node_name
        self.host = host
        self.port = port
        self.validator_data = validator_data

        # Peers
        self.peers = peers
        self.peer_map = {}
        self.peer_conn = {}

        self.is_builder = is_builder
        self.is_validator = is_validator
        for peer in self.peers:
            ek = peer.data.ed25519.encode()
            self.peer_map[ek] = peer

        if is_validator and is_builder:
            raise ValueError("Node can't be validator and builder at same time!")

        self.__id = generate_keys(port)
        self.dns = self.__id

    def __str__(self):
        return f"Node({self.host}:{self.port})"

    def __repr__(self):
        return f"Node(host={self.host}, port={self.port}, id={self.__id})"

    @property
    def ed_key(self):
        return self.validator_data.ed25519

    @property
    def ed_pvt_key(self) -> Ed25519PrivateKey:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        key_file = f"seeds/{self.port}/key.pem"

        # Load the ED25519 private key
        with open(key_file, "rb") as key_file:
            private_key = load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

        return private_key

    def get_peer(self, key: bytes) -> Peer | None:
        if key in self.peer_map:
            return self.peer_map[key]

        return None

    @staticmethod
    def get_initiator(k1: Ed25519Public, k2: Ed25519Public) -> Ed25519Public:
        i1 = int.from_bytes(k1)
        i2 = int.from_bytes(k2)

        if (i1 > 127) ^ (i2 > 127) ^ (i1 < i2):
            print("self init")
            return k1
        else:
            print("peer init")
            return k2

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
            config.alpn_protocols = [builder_alpn]
        else:
            config.alpn_protocols = [node_alpn, builder_alpn]

        return config
    
    async def run_server(self):
        """
        Function to initialize server connection of the node.
        """
        session_ticket_store = SessionTicketStore(self.port)

        logger.info(f"🚀 ({self.name}) Listening on {str(self)}")

        # Start server connection
        server = await serve(
            self.host,
            self.port,
            configuration=self.quic_config(is_client=False),
            create_protocol=lambda *args, **kwargs: QuicProtocol(*args, node=self, **kwargs),
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
        )

        # Save server connection
        self.server = server

    async def quic_connect(self, peer: Peer, delay: int = 0):
        session_ticket_store = SessionTicketStore(self.port)
        if delay:
            logger.warning(f"Connection to {peer} delayed for {delay}s")
            await asyncio.sleep(delay)

        if peer in self.peer_conn:
            logger.info(f"Connection already established.")
            return

        try:
            logger.info(f"🔹 ({self.name}) Creating new connection to {str(peer)} via QUIC...")
            async with connect(
                str(peer.host),
                int(peer.port),
                configuration=self.quic_config(peer=peer),
                create_protocol=lambda *args, **kwargs: QuicProtocol(*args, node=self, **kwargs),
                session_ticket_handler=session_ticket_store.add,
            ) as client:

                # Save peer connection
                client = cast(QuicProtocol, client)

                logger.info(f"🤝 ({self.name}) Connection to {str(peer)} established ✅")

                stream_id = -1
                if not self.is_builder:
                    stream_id = client._quic.get_next_available_stream_id()

                    from jam.network.protocols.up_0 import BlockAnnouncement
                    pref = PrefixType.UP0.encode()
                    client.stream_buffer[stream_id] = pref
                    client.stream_and_keep_open(pref, stream_id)
                    print("here before handshake")
                    BlockAnnouncement.handshake(stream_id, client)


                self.peer_conn[peer] = stream_id, client
                self.is_initialized = True

                # Wait indefinitely - the connection will be managed by the context manager
                await asyncio.Future()

        except Exception as e:
            logger.error(f"Connection to {peer} failed: {e}")

    async def connect_peer(self, peer: Peer):
        """
        Function to connect the node to a peer.
        """

        try:
            # Skip self
            if str(peer.host) == self.host and int(peer.port) == self.port:
                logger.info(f"⚠️ ({self.name}) Skipping self {str(self)}")
                return

            # TODO: Abstract out builder connections
            if int(peer.port) == 40001:
                logger.info(f"⚠️ ({self.name}) Skipping builder {str(peer)}")
                return

            init = self.get_initiator(self.ed_key, peer.ed_key)
            if init == self.ed_key:
                await self.quic_connect(peer)
            else:
                # Try connection after 6 seconds, meanwhile continue forward with other connections
                await self.quic_connect(peer, INIT_DELAY)

        except asyncio.CancelledError:
            logger.info(f"🔴 ({self.name}) Connection with {str(peer)} cancelled")
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
        try:
            if self.is_builder:
                logger.info(f"🚀 ({self.name}) Starting builder on {str(self)}")

            if not self.is_builder:
                logger.info(f"🚀 ({self.name}) Starting server on {str(self)}")
                await self.run_server()

                # Give server time to fully initialize
                await asyncio.sleep(1)

            logger.info(f"🔄 ({self.name}) Opening connections to {len(self.peers)} peers...")
            await self.run_client()

            logger.info(f"🚀 {self} initialized successfully!")
        except Exception as e:
            logger.critical(f"🚀 {self} failed to initialize!")

