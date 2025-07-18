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
from typing import Callable, Dict, Optional, Text, Union, cast
from jam.logging import get_logger
from jam.network.base.jamnp import JAMNP
from jam.network.base.protocol import PrefixType
from jam.types.protocol.validators import ValidatorData


logger = get_logger("network")

# AIOQUIC - Patch to recieve certificates
_original_initialize = QuicConnection._initialize 

def _initialize(self, peer_cid: bytes) -> None:
    _original_initialize(self, peer_cid)
    self.tls._request_client_certificate = True 

QuicConnection._initialize = _initialize


class QuicPeer(asyncio.DatagramProtocol):

    _protocols: Dict[bytes, JAMNP]

    def __init__(
        self,
        *,
        server_cfg: QuicConfiguration,
        client_cfg: QuicConfiguration,
        create_protocol: Callable = JAMNP,
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
        self._server_cfg = server_cfg
        self._client_cfg = client_cfg
        self._create_protocol = create_protocol
        self._loop = asyncio.get_running_loop()
        self._protocols = {}
        self._session_ticket_fetcher = session_ticket_fetcher
        self._session_ticket_handler = session_ticket_handler
        self._transport: Optional[asyncio.DatagramTransport] = None

        self._stream_handler = stream_handler

        if retry:
            self._retry = QuicRetryTokenHandler()
        else:
            self._retry = None

    def close(self) -> None:
        """
        Close any ongoing connections and stop listening.
        """
        for protocol in set(self._protocols.values()):
            protocol.close()
        self._protocols.clear()
        if self._transport: self._transport.close()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(self, data: Union[bytes, Text], addr: NetworkAddress) -> None:
        data = cast(bytes, data)
        buf = Buffer(data=data)

        try:
            header = pull_quic_header(
                buf, host_cid_length=self._server_cfg.connection_id_length
            )
        except ValueError:
            logger.error("Invalid QUIC packet received from %s", addr)
            return

        if not self._transport:
            raise ValueError("Misconfig: Transport is not set")

        # version negotiation
        if (
            header.version is not None
            and header.version not in self._server_cfg.supported_versions
        ):
            self._transport.sendto(
                encode_quic_version_negotiation(
                    source_cid=header.destination_cid,
                    destination_cid=header.source_cid,
                    supported_versions=self._server_cfg.supported_versions,
                ),
                addr,
            )
            return

        protocol = self._protocols.get(header.destination_cid, None)
        original_destination_connection_id: Optional[bytes] = None
        retry_source_connection_id: Optional[bytes] = None
        
        logger.debug("Datagram received", protocol_exists=protocol is not None, addr=addr, packet_type=header.packet_type, cid=header.destination_cid.hex())

        if (
            protocol is None
            and len(data) >= SMALLEST_MAX_DATAGRAM_SIZE
            and header.packet_type == QuicPacketType.INITIAL
            # is_client enabled server shouldn't accept unknown connections 
            and not self._server_cfg.is_client
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

            # create new connection
            logger.debug("Creating new server connection", address=addr)
            
            connection = QuicConnection(
                configuration=self._server_cfg,
                original_destination_connection_id=original_destination_connection_id,
                retry_source_connection_id=retry_source_connection_id,
                session_ticket_fetcher=self._session_ticket_fetcher,
                session_ticket_handler=self._session_ticket_handler,
            )
            protocol = self._create_protocol(quic=connection)
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

            self._protocols[header.destination_cid] = protocol
            self._protocols[connection.host_cid] = protocol

            connection._logger = logger
            print(f"Created server connection with CID {connection.host_cid.hex()}")
            
        if protocol is not None:
            logger.debug("Processing datagram", data_len=len(data), connection_id=protocol._quic.host_cid.hex())
            protocol.datagram_received(data, addr)

    def _connection_id_issued(self, cid: bytes, protocol: QuicConnectionProtocol):
        logger.debug(f"Connection ID issued", cid=cid.hex())
        self._protocols[cid] = protocol


    def _connection_id_retired(
        self, cid: bytes, protocol: QuicConnectionProtocol
    ) -> None:
        assert self._protocols[cid] == protocol
        del self._protocols[cid]

    def _connection_terminated(self, protocol: QuicConnectionProtocol):
        for cid, proto in list(self._protocols.items()):
            if proto == protocol:
                del self._protocols[cid]
    
    async def connect(self, peer: ValidatorData) -> QuicConnectionProtocol|None:
        # Only if we are the initiator
        from jam.settings import settings
        if (
            (peer.ed25519[31] > 127) ^ 
            (settings.ed25519_public[31] > 127) ^ 
            (int.from_bytes(peer.ed25519) < int.from_bytes(settings.ed25519_public))
        ):
            return None;

        addr = (str(peer.metadata.host), int(peer.metadata.port))
        quic = QuicConnection(configuration=self._client_cfg)
        protocol = self._create_protocol(val_=peer, quic=quic)
        protocol.connection_made(self._transport)      # share transport
        self._protocols[quic.host_cid] = protocol  # register protocol
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
        logger.debug(f"Creating new client connection", addr=addr, cid=quic.host_cid.hex())
        protocol.connect(addr)                        # start handshake
        protocol.transmit()                           # send initial flight
        await protocol.wait_connected()
        logger.debug(f"Connected to {addr}", cid=quic.host_cid.hex())
        
        # --- Ping UP0 --- #
        stream_id = protocol._quic.get_next_available_stream_id()
        protocol.up0_stream = stream_id
        pref = PrefixType.UP0.encode()
        protocol.stream_buffer[stream_id] = pref
        protocol.stream_and_keep_open(pref, stream_id)
        return protocol
