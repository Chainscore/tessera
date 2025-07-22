from typing import List, Set
import math
from _pytest.nodes import Node
from aioquic.quic.retry import QuicRetryTokenHandler
from aioquic.quic.connection import NetworkAddress
from aioquic._buffer import Buffer
from aioquic.quic.packet import pull_quic_header
from aioquic.quic.packet import encode_quic_version_negotiation
from aioquic.quic.packet import QuicPacketType
from aioquic.quic.configuration import SMALLEST_MAX_DATAGRAM_SIZE
from aioquic.quic.packet import encode_quic_retry
from aioquic.quic.connection import QuicConnection
from aioquic.asyncio.protocol import QuicStreamHandler
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.tls import SessionTicketHandler
from aioquic.tls import SessionTicketFetcher
from aioquic.quic.configuration import QuicConfiguration
import asyncio
import os
from functools import partial
from typing import Callable, Optional, Text, Union, cast
from jam.logging import get_logger
from jam.network.base.protocol import PrefixType
from jam.types.protocol.crypto import Ed25519Public
from jam.utils.constants import VALIDATOR_COUNT
from .connection import NodeConnection
from jam.types.protocol.validators import ValidatorData


logger = get_logger("quic")

# AIOQUIC - Patch to recieve certificates
_original_initialize = QuicConnection._initialize

def _initialize(self, peer_cid: bytes) -> None:
    _original_initialize(self, peer_cid)
    self.tls._request_client_certificate = True

QuicConnection._initialize = _initialize


class QuicNode(asyncio.DatagramProtocol):
    # SAN
    _id: str
    # (cached) List of neighbor validator keys
    neighbors: List[Ed25519Public]
    # Ed25519 key to Connection ID
    # : Needed for when we want to send data to a specific validator
    conns: dict[Ed25519Public, bytes]
    # Connection ID -> Validator index mapping
    # : Essential for fast access from datagram_received
    connection_ids: dict[bytes, NodeConnection]
    # port
    port: int

    def __init__(
        self,
        *,
        id: str,
        cfg: QuicConfiguration,
        create_protocol: Callable = NodeConnection,
        session_ticket_fetcher: Optional[SessionTicketFetcher] = None,
        session_ticket_handler: Optional[SessionTicketHandler] = None,
        retry: bool = False,
        stream_handler: Optional[QuicStreamHandler] = None,
    ) -> None:
        """
        QuicPeer requires a :class:`~aioquic.quic.configuration.QuicConfiguration`
        containing TLS certificate and private key as the ``configuration`` argument.

        This also accepts the following arguments:

        * ``create_protocol`` allows customizing the :class:`~asyncio.Protocol` that
          manages the connection. It should be a callable or class accepting the same
          arguments as :class:`~aioquic.asyncio.QuicConnectionProtocol` and returning
          an instance of :class:`~aioquic.asyncio.QuicConnectionProtocol` or a subclass.
        * ``session_ticket_fetcher`` (Optional) is a callback which is invoked by the TLS
          engine when a session ticket is presented by the peer. It should return
          the session ticket with the specified ID or `None` if it is not found.
        * ``session_ticket_handler`` (Optional) is a callback which is invoked by the TLS
          engine when a new session ticket is issued. It should store the session
          ticket for future lookup.
        * ``retry`` (Optional) specifies whether client addresses should be validated prior to
          the cryptographic handshake using a retry packet.
        * ``stream_handler`` (Optional) is a callback which is invoked whenever a stream is
          created. It must accept two arguments: a :class:`asyncio.StreamReader`
          and a :class:`asyncio.StreamWriter`.
        """
        self._id = id
        self._cfg = cfg
        self._create_protocol = create_protocol
        self._loop = asyncio.get_running_loop()
        self.connection_ids = {}
        self.conns = {}
        self.neighbors = []

        self._session_ticket_fetcher = session_ticket_fetcher
        self._session_ticket_handler = session_ticket_handler
        self._transport: Optional[asyncio.DatagramTransport] = None

        self._stream_handler = stream_handler

        if retry:
            self._retry = QuicRetryTokenHandler()
        else:
            self._retry = None

    def set_neighbors(self) -> None:
        """
        Set our neighbors. To be triggered at every epoch change.
        """
        from jam.state.state import state
        from jam.settings import settings
        w = math.floor(math.sqrt(VALIDATOR_COUNT))
        index = settings.validator_index
        row = index // w
        col = index % w
        neighbors = set([
            k for i, k in enumerate(state.kappa)
            if (i // w == row or i % w == col) and i != index
        ])
        neighbors.add(state.lambda_[index])
        neighbors.add(state.gamma.k[index])
        neighbors.add(state.iota[index])

        neighbors = [n for n in neighbors if n.ed25519 != settings.ed25519_public]
        logger.info("🏠 Neighbors set", neighbors=[n.metadata.port for n in neighbors], count=len(neighbors))
        # Convert to list and save
        self.neighbors = list([n.ed25519 for n in neighbors])

    def close(self) -> None:
        """
        Close any ongoing connections and stop listening.
        """
        for protocol in self.connection_ids.values():
            protocol.close()
        self.conns = {}
        self.connection_ids = {}
        self.neighbors = []
        if self._transport: self._transport.close()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(self, data: Union[bytes, Text], addr: NetworkAddress) -> None:
        data = cast(bytes, data)
        buf = Buffer(data=data)

        try:
            header = pull_quic_header(
                buf, host_cid_length=self._cfg.connection_id_length
            )
        except ValueError:
            logger.error("Invalid QUIC packet received from %s", addr)
            return

        if not self._transport:
            raise ValueError("Misconfig: Transport is not set")

        # version negotiation
        if (
            header.version is not None
            and header.version not in self._cfg.supported_versions
                ):
            self._transport.sendto(
                encode_quic_version_negotiation(
                    source_cid=header.destination_cid,
                    destination_cid=header.source_cid,
                    supported_versions=self._cfg.supported_versions,
                ),
                addr,
            )
            return

        protocol = self.connection_ids.get(header.destination_cid, None)
        original_destination_connection_id: Optional[bytes] = None
        retry_source_connection_id: Optional[bytes] = None

        # logger.debug("Datagram received", protocol_exists=protocol is not None, addr=addr, packet_type=header.packet_type, cid=header.destination_cid.hex(), data_len=len(data))

        if (
            protocol is None and
            len(data) >= SMALLEST_MAX_DATAGRAM_SIZE
            and header.packet_type == QuicPacketType.INITIAL
            # TODO: Builder shouldn't accept incoming connections
            # is_client enabled server shouldn't accept unknown connections
            # and not self._server_cfg.is_client
        ):
            # retry
            if self._retry is not None:
                if not header.token:
                    # create a retry token
                    source_cid = os.urandom(8)
                    self._transport.sendto(
                        encode_quic_retry(
                            version=header.version,
                            source_cid=source_cid,
                            destination_cid=header.source_cid,
                            original_destination_cid=header.destination_cid,
                            retry_token=self._retry.create_token(
                                addr, header.destination_cid, source_cid
                            ),
                        ),
                        addr,
                    )
                    return
                else:
                    # validate retry token
                    try:
                        (
                            original_destination_connection_id,
                            retry_source_connection_id,
                        ) = self._retry.validate_token(addr, header.token)
                    except ValueError:
                        return
            else:
                original_destination_connection_id = header.destination_cid

            # Create a server config from the original configuration
            server_cfg = QuicConfiguration(**self._cfg.__dict__)
            server_cfg.is_client = False  # Server side
            connection = QuicConnection(
                configuration=server_cfg,
                original_destination_connection_id=original_destination_connection_id,
                retry_source_connection_id=retry_source_connection_id,
                session_ticket_fetcher=self._session_ticket_fetcher,
                session_ticket_handler=self._session_ticket_handler,
            )
            protocol = self._create_protocol(quic=connection, is_initiating=False, port=addr[1])
            protocol.connection_made(self._transport)

            # register callbacks
            protocol._connection_id_issued_handler = partial(
                self._connection_id_issued, protocol=protocol
            )
            protocol._connection_id_retired_handler = partial(
                self._connection_id_retired, protocol=protocol
            )
            protocol._connection_terminated_handler = partial(
                self._connection_terminated, protocol=protocol
            )

            self.connection_ids[header.destination_cid] = protocol
            self.connection_ids[connection.host_cid] = protocol

            connection._logger = logger
            logger.info(f"⬅️ Created server connection with {addr[1]}", CID=connection.host_cid.hex())

        if protocol is not None:
            logger.debug("🌸Processing datagram", data_len=len(data), connection_id=protocol._quic.host_cid.hex())
            protocol.datagram_received(data, addr)

    def _connection_id_issued(self, cid: bytes, protocol: NodeConnection):
        logger.debug(f"Connection ID issued", cid=cid.hex())
        self.connection_ids[cid] = protocol
        if protocol.ed25519_public:
            self.conns[protocol.ed25519_public] = cid
        # # Delete the old connection ID. Find by protocol
        # for old_cid, old_protocol in list(self.connection_ids.items()):
        #     if old_protocol == protocol and old_cid != cid:
        #         logger.debug(f"Deleting old connection ID", old_cid=old_cid.hex(), new_cid=cid.hex())
        #         del self.connection_ids[old_cid]

    def _connection_id_retired(
        self, cid: bytes, protocol: QuicConnectionProtocol
    ) -> None:
        assert self.connection_ids[cid] == protocol
        del self.connection_ids[cid]
        logger.debug(f"Connection ID retired", cid=cid.hex())

    @property
    def active_peers(self) -> Set[NodeConnection]:
        return set([
            self.connection_ids[self.conns[k]]
            for k in self.neighbors
            if self.conns.get(k) and self.connection_ids.get(self.conns.get(k))
        ])

    @property
    def all_connected(self) -> Set[NodeConnection]:
        return set([
            conn
            for _, conn in self.connection_ids.items()
            if conn.ed25519_public
        ])

    def _connection_terminated(self, protocol: NodeConnection):
        for cid, proto in list(self.connection_ids.items()):
            if proto == protocol:
                del self.connection_ids[cid]

        if not protocol.ed25519_public:
            logger.warning("Connection terminated without public key", cid=protocol._quic.host_cid.hex())
            return
        from jam.state.state import state
        val = state.kappa.find(protocol.ed25519_public)[1]
        if not val:
            logger.warning("Connection terminated for a non active validator", cid=protocol._quic.host_cid.hex(), ed25519=protocol.ed25519_public.hex())
            return
        asyncio.create_task(self.connect(val))

    async def connect(self, peer: ValidatorData) -> QuicConnectionProtocol|None:
        # Only if we are the initiator
        from jam.settings import settings

        addr = (str(peer.metadata.host), int(peer.metadata.port))

        if (
            (peer.ed25519[31] > 127) ^
            (settings.ed25519_public[31] > 127) ^
            (int.from_bytes(peer.ed25519) < int.from_bytes(settings.ed25519_public))
        ):
            return None

        quic = QuicConnection(configuration=self._cfg)
        protocol: NodeConnection = self._create_protocol(quic=quic, is_initiating=True, port=peer.metadata.port)
        protocol.connection_made(self._transport)       # share transport
        self.connection_ids[quic.host_cid] = protocol   # register protocol
        self.conns[peer.ed25519] = quic.host_cid        # register connection ID
        protocol._connection_id_issued_handler = partial(
            self._connection_id_issued, protocol=protocol
        )
        protocol._connection_id_retired_handler = partial(
            self._connection_id_retired, protocol=protocol
        )
        protocol._connection_terminated_handler = partial(
            self._connection_terminated, protocol=protocol
        )
        # --- Connect --- #
        protocol.connect(addr)                        # start handshake
        protocol.transmit()                           # send initial flight
        await protocol.wait_connected()
        logger.info(f"➡️ Created client connection with {addr[1]}", cid=quic.host_cid.hex())

        protocol.up0_stream = 0
        protocol.stream_and_keep_open(bytes(1), protocol.up0_stream)
        asyncio.create_task(self.keep_pinging(protocol))

        # stream_id = protocol._quic.get_next_available_stream_id()
        # from jam.network.protocols import BlockAnnouncement
        # BlockAnnouncement.handshake(stream_id, protocol, True)

        return protocol

    async def keep_pinging(self, conn: NodeConnection, period = 10):
        while True:
            await conn.ping()
            await asyncio.sleep(period)
