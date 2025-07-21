import asyncio
import ssl
import socket

from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.logging import get_logger

from jam.types.protocol.validators import ValidatorData, ValidatorsData
from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import Ed25519Public
from jam.types.work.shard import ShardIndex

from typing import Dict, cast, Tuple, Optional

from .asyncio.client import connect
from .asyncio.server import QuicServer, serve
from .base.quic import QuicProtocol
from jam.network.base.certificate import generate_keys
from jam.network.base.protocol import PrefixType
from jam.network.base.sessions import SessionTicketStore
from jam.utils import constants
from .peer import Peer

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
    peer_conn: Dict[Peer, Tuple[int | None, QuicProtocol]] = {}
    builder_conn: Dict[QuicProtocol, int] = {}
    max_builders: int

    # Server
    server: QuicServer

    # Flags
    is_initialized: bool = False
    is_builder: bool = False
    is_validator: bool = True

    def __init__(
        self,
        node_name: str,
        host: str,
        port: int,
        validator_data: ValidatorData,
        peers: list[Peer],
        is_builder: bool,
        is_validator: bool,
    ):
        self.name = node_name
        self.host = host
        self.port = int(port)
        self.validator_data = validator_data

        self.max_builders = 20

        # Peers
        self.peers = peers
        self.peer_map = {}
        self.peer_conn = {}
        self.builder_conn = {}

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
    def b_key(self):
        return self.validator_data.bandersnatch

    @property
    def ed_pvt_key(self) -> Ed25519PrivateKey:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        key_file = f"seeds/{self.port}/key.pem"

        # Load the ED25519 private key
        with open(key_file, "rb") as key_file:
            private_key = load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )

        return private_key

    def get_peer(self, key: bytes) -> Peer | None:
        if key in self.peer_map:
            return self.peer_map[key]

        return None

    @property
    def validator_index(self):
        from jam.state.state import state

        for i, val in enumerate(state.kappa):
            if val.bandersnatch == self.validator_data.bandersnatch:
                return i

        raise ValueError("No validator found with matching bandersnatch key.")

    def get_shard_index(self, core_index: CoreIndex):
        from jam.utils.chainspec import chain_config

        vi = self.validator_index
        shard_index = ShardIndex(
            (core_index * chain_config.recovery_threshold + vi)
            % constants.VALIDATOR_COUNT
        )

        return shard_index

    @staticmethod
    def get_initiator(k1: Ed25519Public, k2: Ed25519Public) -> Ed25519Public:
        i1 = int.from_bytes(k1)
        i2 = int.from_bytes(k2)

        if (i1 > 127) ^ (i2 > 127) ^ (i1 < i2):
            logger.debug("Self node is connection initiator")
            return k1
        else:
            logger.debug("Peer node is connection initiator")
            return k2

    def quic_config(
        self, is_client: bool = True, peer: Optional[Peer] = None
    ) -> QuicConfiguration:
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
        config.load_cert_chain(
            f"seeds/{self.port}/cert.pem", f"seeds/{self.port}/key.pem"
        )
        config.verify_mode = ssl.CERT_NONE

        config.max_data = 104857600  # 100 MB
        config.max_stream_data = 10485760  # 10 MB per stream
        config.idle_timeout = 120.0

        if is_client:
            config.server_name = self.__id

        if self.is_builder:
            config.alpn_protocols = [builder_alpn]
        else:
            config.alpn_protocols = [node_alpn, builder_alpn]

        return config

    async def run_server(self, sock = None):
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
            create_protocol=lambda *args, **kwargs: QuicProtocol(
                *args, node=self, **kwargs
            ),
            retry=True,
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
            sock=sock
        )

        # Save server connection
        self.server = server

    async def quic_connect(self, peer: Peer, sock = None, delay: int = 0):
        session_ticket_store = SessionTicketStore(self.port)
        if delay:
            logger.warning(f"Connection to {peer} delayed for {delay}s")
            await asyncio.sleep(delay)

        if peer in self.peer_conn:
            logger.info(f"Connection already established.")
            return

        try:
            logger.info(
                f"🔹 ({self.name}) Creating new connection to {str(peer)} via QUIC..."
            )
            async with connect(
                str(peer.host),
                int(peer.port),
                configuration=self.quic_config(peer=peer),
                create_protocol=lambda *args, **kwargs: QuicProtocol(
                    *args, node=self, **kwargs
                ),
                # wait_connected=False,
                session_ticket_handler=session_ticket_store.add,
                # local_port=int(self.port),
                sock=sock
            ) as client:

                # Save peer connection
                client = cast(QuicProtocol, client)

                logger.info(
                    f"🤝 Connection to {str(peer)} established ✅"
                )

                stream_id = -1
                if not self.is_builder:
                    stream_id = client._quic.get_next_available_stream_id()

                    from jam.network.protocols.up_0 import BlockAnnouncement

                    pref = PrefixType.UP0.encode()
                    client.stream_buffer[stream_id] = pref
                    client.stream_and_keep_open(pref, stream_id)
                    BlockAnnouncement.handshake(stream_id, client)

                self.peer_conn[peer] = stream_id, client
                self.is_initialized = True
                print("initialized less go")
                # Wait indefinitely - the connection will be managed by the context manager
                await asyncio.Future()

        except Exception as e:
            logger.error(f"Connection to {peer} failed: {e}")

    async def connect_peer(self, peer: Peer, sock = None):
        """
        Function to connect the node to a peer.
        """

        try:
            # Skip self
            logger.info(f"⚠️ ({self.name}) host: {self.host}, port: {self.port}, {str(peer)} {type(self.port)}", hostcomp=(str(peer.host) == self.host), portcomp=(peer.port == self.port))
            if str(peer.host) == self.host and int(peer.port) == self.port:
                logger.info(f"⚠️ ({self.name}) Skipping self {str(self)}")
                return

            if self.is_builder:
                # Directly connect to peer
                await self.quic_connect(peer)
                return

            # Fetch initiator
            init = self.get_initiator(self.ed_key, peer.ed_key)
            if init == self.ed_key:
                await self.quic_connect(peer, sock)
            else:
                # Try connection after 6 seconds, meanwhile continue forward with other connections
                await self.quic_connect(peer, sock, INIT_DELAY)

        except asyncio.CancelledError:
            logger.info(f"🔴 ({self.name}) Connection with {str(peer)} cancelled")
        except Exception as e:
            logger.warning(f"⚠️ ({self.name}) Failed to connect to {peer}: {e}")

    async def run_client(self, sock = None):
        """
        Function to initialize client connections of the node.
        """
        tasks = []
        for peer in self.peers:
            tasks.append(asyncio.create_task(self.connect_peer(peer, sock)))
        await asyncio.gather(*tasks)

    async def initialize(self):
        """
        Function to fully initialize a node.
        """

        # Create Socket Connection
        # explicitly enable IPv4/IPv6 dual stack
        local_host = "::"
        # sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        # completed = False
        # try:
        #     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        #     sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        #     sock.bind((local_host, self.port, 0, 0))
        #     completed = True
        #     logger.info("Bound to socket successfully!")
        #
        # except Exception as e:
        #     logger.error("Unable to bind with socket", err = e)
        #
        # finally:
        #     if not completed:
        #         logger.error("Unable to bind with socket. Closing socket")
        #         sock.close()

        sock = None

        # sock = None
        try:
            if self.is_builder:
                logger.info(f"🚀 ({self.name}) Starting builder on {str(self)}")


            if not self.is_builder:
                logger.info(f"🚀 ({self.name}) Starting server on {str(self)}")
                await self.run_server(sock)

                # Give server time to fully initialize
                await asyncio.sleep(1)

            logger.info(
                f"🔄 ({self.name}) Opening connections to {len(self.peers)} peers..."
            )
            await self.run_client(sock)

            logger.info(f"🚀 {self} initialized successfully!")
        except Exception as e:
            logger.critical(f"🚀 {self} failed to initialize!", err=e)

    def shutdown(self):
        for peer in self.peer_conn:
            _, conn = self.peer_conn[peer]
            conn.close(reason_phrase=f"Closing node {self.__id}")

node = Node("god", "127.0.0.1", 0, ValidatorsData.decode(bytes(10000)), [], False, False)

def setup_node(name, port, peers, is_val = True, is_bd = False, host="127.0.0.1") -> Node:
    global node
    from jam.settings import settings
    node = Node(name, host, port, settings.val, peers, is_bd, is_val)
    return node
