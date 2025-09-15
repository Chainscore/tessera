import asyncio
from typing import Dict, Optional

from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.asyncio.protocol import QuicStreamHandler
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import (
    QuicEvent,
    StreamDataReceived,
    ConnectionTerminated,
    HandshakeCompleted,
    ConnectionIdIssued,
    ConnectionIdRetired,
    StreamReset,
    StopSendingReceived,
)
from tsrkit_types import U8
from jam.logging import network_logger
from jam.network.base.certificate import verify_certificate, generate_san
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import PrefixType

from jam.types.protocol.core import CoreIndex, ValidatorIndex
from jam.types.protocol.crypto import Ed25519Public
from jam.types.work.shard import ShardIndex
from jam.utils.constants import VALIDATOR_COUNT, NODE_ALPN

genesis_hash = "476243ad"
protocol_version = "0"

# Module-specific logger
logger = network_logger


class NodeConnection(QuicConnectionProtocol):
    """JAMNP-spec QUIC Connection handler"""
    # SAN
    _id: str
    # Common UP0 Stream ID. 
    # If not None, we have connected UP0 
    up0_stream: Optional[int] = None
    # Stream buffers 
    stream_buffer: Dict[int, bytes] = {}
    stream_prefix: Dict[int, int] = {}
    # Key we discoeverd during TLS handshake. 
    # If not None, we know its verified
    ed25519_public = None 
    # Have we completed the UP0 handshake  
    handshake_completed = False
    # If we are initiating the connection
    is_initiating = False
    port = None

    def __repr__(self):
        return (
            f"Node(host={str(self.val.metadata.host)}, port={int(self.val.metadata.port)}, san={str(self._id)})"
        )

    def __init__(
        self, 
        _id: str,
        quic: QuicConnection, 
        is_initiating: bool,
        port: int,
        stream_handler: QuicStreamHandler|None = None
    ) -> None:
        super().__init__(quic=quic, stream_handler=stream_handler)
        self._id = _id
        self.waiter = {}
        self.stream_buffer = {}
        self.stream_prefix = {}
        self._close_pending = False

        self.up0_stream = None 
        self.ed25519_public = None
        self.handshake_completed = False
        self.is_initiating = is_initiating
        self.port = port

    def verify_cert(self) -> Ed25519Public|None:
        """
        Verify the peer's certificate and extract the public key.
        To be called upon the HandshakeCompleted 
        """
        try:
            peer_cert = self._quic.tls._peer_certificate
            if not peer_cert:
                raise ValueError("No peer cert found in TLS handshake.")

            # Verify certificate 
            is_valid, e = verify_certificate(peer_cert)
            if not is_valid:
                raise ValueError("Certificate is not valid", e)
            
            pk = Ed25519Public(peer_cert.public_key().public_bytes_raw())
            logger.info(f"🔗 Handshake completed with {pk.hex()}.")

            self.ed25519_public = pk 
            self._id = generate_san(pk)
            return pk 
        
        except Exception as e:
            logger.error(f"❌ Error during certificate verification: {e}")
            self._quic.close(error_code=0xA, reason_phrase="Certificate verification failed.")
            return None

    def stop_stream(self, stream_id: int, error_code: int):
        self._quic.stop_stream(stream_id, error_code)

    def stream_and_keep_open(self, message: bytes, stream_id: Optional[int] = None) -> int:
        """function for streaming data without end stream (FIN) bit."""
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()
            if stream_id == self.up0_stream or (self.up0_stream is None and stream_id == 0):
                stream_id += 4

        logger.debug(
            f"📤 Sending message of size {len(message)} bytes",
            stream_id=stream_id,
        )

        self._quic.send_stream_data(stream_id, message, end_stream=False)

        self.transmit()
        return stream_id

    def stream_and_close(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        """function for streaming data with end stream (FIN) bit. used by request interceptors."""
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        logger.debug(f"📤 Sending message of size {len(message)} bytes.", stream_id=stream_id)

        self._quic.send_stream_data(stream_id, message, end_stream=True)
        self.transmit()

    async def close_and_wait(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        """function for streaming data with end stream (FIN) bit and waiting for response. used by request transmitters."""
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        logger.debug(f"📤 Sending message of size {len(message)} bytes.", stream_id=stream_id)
        self._quic.send_stream_data(stream_id, message, end_stream=True)

        try:
            waiter = self._loop.create_future()
            self.waiter[stream_id] = waiter
            self.transmit()

            logger.debug("Message transmitted, waiting for response", stream_id=stream_id)
            return await asyncio.shield(waiter)

        except Exception as e:
            logger.error(
                "Error occurred while waiting for response",
                error=str(e),
                error_type=str(type(e)),
                stream_id=stream_id,
            )

            # TODO: Wait for responses for a certain timeout
            # try:
            #     return await asyncio.wait_for(asyncio.shield(waiter), timeout=timeout)
            # except asyncio.TimeoutError:
            #     logger.warning(f"⏱️ Timeout waiting for stream {stream_id} response")
            #     del self.waiter[stream_id]
            #     return None

    def quic_event_received(self, event: QuicEvent) -> None:
        """function that handles all the quic events"""

        logger.debug("Received QUIC Event", name=type(event).__name__)

        # Handle TLS Handshake
        if isinstance(event, HandshakeCompleted):
            self.is_initialized = True
            # Verify Certificate & fetch Peer info
            if event.alpn_protocol and not event.alpn_protocol.startswith(NODE_ALPN):
                logger.error(f"Unsupported ALPN protocol: {event.alpn_protocol}")
                return self._quic.close()
            
            if not self.ed25519_public: self.verify_cert()
            # from .start import node 
            # # Only if we are a non-initaiting neighbor, we need to do reverse up0 handshake 
            # if node and pk in node.neighbors and not self.is_initiating:
            #     self.has_pending_handshake = True
            # else: 
            #     logger.debug("Node is not a neighbor, no pending handshake required.")
            #     self.has_pending_handshake = False

        # Handle Stream Reset Event
        elif isinstance(event, (StreamReset, StopSendingReceived)):
            stream_id = event.stream_id
            if stream_id in self.stream_buffer:
                del self.stream_buffer[stream_id]
            logger.warning(f"🔗 Stream flushed", event_=type(event).__name__)

        # Handle Received Data Event
        elif isinstance(event, StreamDataReceived):
            from jam.network.base.protocol_map import ProtocolMap

            if not self.ed25519_public:
                self.verify_cert()

            # Fetch peer & data
            stream_id = event.stream_id
            data = event.data

            if not self.ed25519_public:
                raise NetworkingError(Code.NO_PEER)


            # -------------------- FIRST HANDLE THE BUFFER --------------------
            # If we don't know stream, we receive prefix
            # i.e. whenever client initiates connection or starts new protocol.
            # Add prefix to the buffer
            prefix = U8.decode(data)
            logger.debug(
                f"📥 Received data",
                stream_id=stream_id,
                prefix=prefix,
                data_len=len(data)
            )

            from jam.network.start import node
            assert node, "Node must be initialized before handling streams."

            if self.up0_stream is None and self.ed25519_public in node.neighbors and prefix == PrefixType.UP0:
                # Send UP0 Handshake 
                from jam.network.protocols.up_0 import BlockAnnouncement 

                BlockAnnouncement().handshake(stream_id, self)
                self.up0_stream = stream_id
                if len(data) == 1:
                    return
                data = data[1:]

            
            if self.up0_stream == event.stream_id:
                from jam.network.protocols.up_0 import BlockAnnouncement 
                BlockAnnouncement().req_intercept(stream_id, self, data)
                return
            
            if stream_id not in self.stream_buffer:
                self.stream_buffer[stream_id] = b""
                self.stream_prefix[stream_id] = prefix
            self.stream_buffer[stream_id] += data

            if not event.end_stream:
                return           
            try:
                prefix = U8(self.stream_prefix[stream_id])

                # Map the request to its corresponding CE protocol function
                ce_protocol = ProtocolMap.get_protocol(prefix)()
                logger.debug(f"CE PROTOCOL TRIGGERED", p=type(ce_protocol).__name__)
                if (stream_id in self.waiter) and (self.waiter[stream_id] is not None):
                    logger.debug(
                        "Intercepting Response.",
                        protocol=prefix,
                        stream_id=stream_id,
                    )
                    res = ce_protocol.res_intercept(stream_id, self)

                    # Wait for acknowledgment
                    waiter = self.waiter[stream_id]
                    del self.waiter[stream_id]
                    waiter.set_result(res)

                else:
                    logger.debug(
                        "Intercepting Request.",
                        protocol=prefix,
                        stream_id=stream_id,
                    )
                    ce_protocol.req_intercept(stream_id, self)

                # Clear buffer
                self.stream_buffer.pop(stream_id, None)

            except Exception as e:
                # Clear waiter
                logger.exception(
                    f"Error retrieving data from CE stream.",
                    error=str(e),
                    prefix=prefix,
                )

                if self.waiter[stream_id] is not None:
                    waiter = self.waiter[stream_id]
                    del self.waiter[stream_id]
                    waiter.set_result("failed to retrieve data")

                # Clear buffer
                self.stream_buffer.pop(stream_id, None)

    @property
    def validator_index(self):
        from jam.state.state import state
        for i, val in enumerate(state.kappa):
            if val.ed25519 == self.ed25519_public:
                return ValidatorIndex(i)

        raise ValueError("No validator found with matching ed25519 key.")

    @property
    def val(self):
        from jam.state.state import state
        validator_index = self.validator_index
        return state.kappa[validator_index]

    def get_shard_index(self, core_index: CoreIndex):
        from jam.utils.chainspec import chain_config

        vi = self.validator_index
        shard_index = ShardIndex(
            (core_index * chain_config.recovery_threshold + vi)
            % VALIDATOR_COUNT
        )

        return shard_index