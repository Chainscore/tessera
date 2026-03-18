import asyncio
from enum import IntEnum
from typing import Dict, Optional, TYPE_CHECKING

import structlog
from aioquic.asyncio.protocol import QuicConnectionProtocol, QuicStreamHandler
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

from jam.utils.task_utils import create_safe_task
from tsrkit_types import U8
from jam.network.base.certificate import verify_certificate, generate_san
from jam.network.base.protocol import PrefixType, NetworkProtocol

from jam.types.protocol.core import CoreIndex, ValidatorIndex
from jam.types.protocol.crypto import Ed25519Public
from jam.types.work.shard import ShardIndex
from jam.utils.constants import VALIDATOR_COUNT, NODE_ALPN

if TYPE_CHECKING:
    from jam.jam_node import JamNode

genesis_hash = "476243ad"
protocol_version = "0"


class PeerStatus(IntEnum):
    DISCONNECTING = -2
    FAILED = -1
    DISCONNECTED = 0
    INITIATING = 1
    HANDSHAKE_COMPLETED = 2
    LIVE = 3


class PeerConnection(QuicConnectionProtocol):
    """JAMNP-spec QUIC Connection handler"""

    # Conn Props
    peer_id: str
    peer_ed_key = None
    is_initiator = False

    # Common UP0 Stream ID.
    # If not None, we have connected UP0
    up0_handshake_completed: Optional[bool] = False
    up0_stream: Optional[int] = None
    # Stream buffers
    stream_buffer: Dict[int, bytes] = {}
    stream_prefix: Dict[int, int] = {}

    # If we are initiating the connection
    port = None

    def __repr__(self):
        return f"Node(host={str(self.val.metadata.host)}, port={int(self.val.metadata.port)}, san={str(self.peer_id)})"

    def __init__(
        self,
        _id: str,
        quic: QuicConnection,
        port: int,
        jam_node: "JamNode",
        is_initiator: bool = False,
        stream_handler: QuicStreamHandler | None = None,
    ) -> None:
        super().__init__(quic=quic, stream_handler=stream_handler)
        # Connection Props
        self.is_initiator = is_initiator
        self.peer_id = _id
        self.up0_handshake_completed = None
        self.peer_ed_key = None

        self.up0_stream = None

        # Node props
        self.port = port
        self.jam = jam_node

        # Buffer Handlers
        self.waiter = {}
        self.stream_buffer = {}
        self.stream_prefix = {}

        # Logger
        self.logger = structlog.get_logger("network")

    def verify_cert(self) -> Ed25519Public | None:
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
            self.peer_id = generate_san(pk)

            self.logger = self.logger.bind(peer=self.peer_id)
            self.logger.debug(
                f"🤝 Handshake completed with {pk.hex()}.",
                cert_issuer=str(peer_cert.issuer),
                cert_valid_upto=str(peer_cert.not_valid_after_utc),
            )

            self.peer_ed_key = pk
            return pk

        except Exception as e:
            self.logger.error(f"❌ Error during certificate verification: {e}")
            self._quic.close(error_code=0xA, reason_phrase="Certificate verification failed.")
            return None

    def stop_stream(self, stream_id: int, error_code: int):
        self.logger.debug(
            f"✖ Stopping Stream.", stream_id=stream_id, error_code=error_code
        )

        self._quic.stop_stream(stream_id, error_code)

    def stream_and_keep_open(self, message: bytes, stream_id: Optional[int] = None) -> int:
        """function for streaming data without end stream (FIN) bit."""
        if self._quic._close_pending:
            raise ConnectionError("Connection is either closing or already closed.")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()
            if stream_id == self.up0_stream or (self.up0_stream is None and stream_id == 0):
                stream_id += 4

        self.logger.trace(
            f"📤 Sending message of size {len(message)} bytes",
            stream_id=stream_id,
        )

        self._quic.send_stream_data(stream_id, message, end_stream=False)

        self.transmit()
        return stream_id

    def stream_and_close(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        """function for streaming data with end stream (FIN) bit. used by request interceptors."""
        if self._quic._close_pending:
            raise ConnectionError("Connection is either closing or already closed.")

        self.logger.trace(f"📤 Sending message of size {len(message)} bytes.", stream_id=stream_id)

        self._quic.send_stream_data(stream_id, message, end_stream=True)
        self.transmit()

    async def close_and_wait(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        """function for streaming data with end stream (FIN) bit and waiting for response. used by request transmitters."""
        if self._quic._close_pending:
            raise ConnectionError("Connection is either closing or already closed.")

        self.logger.trace(f"📤 Sending message of size {len(message)} bytes.", stream_id=stream_id)

        self._quic.send_stream_data(stream_id, message, end_stream=True)

        try:
            waiter = self._loop.create_future()
            self.waiter[stream_id] = waiter
            self.transmit()

            result = await asyncio.shield(waiter)
            return result

        except Exception as e:
            # Clean up the waiter to prevent "Future exception was never retrieved"
            if stream_id in self.waiter:
                del self.waiter[stream_id]

            self.logger.error(
                "Error occurred while waiting for response",
                error=str(e),
                error_type=str(type(e)),
                stream_id=stream_id,
            )

            # TODO: Wait for responses for a certain timeout
            # try:
            #     return await asyncio.wait_for(asyncio.shield(waiter), timeout=timeout)
            # except asyncio.TimeoutError:
            #     self.logger.warning(f"⏱️ Timeout waiting for stream {stream_id} response")
            #     del self.waiter[stream_id]
            #     return None

    def quic_event_received(self, event: QuicEvent) -> None:
        """function that handles all the quic events"""
        try:
            self.logger.trace("Received QUIC Event", name=type(event).__name__)

            jam_node = self.jam
            router = self.jam.router
            node = router.node
            state = jam_node.state

            # Handle TLS Handshake
            if isinstance(event, HandshakeCompleted):
                # Verify Certificate & fetch Peer info
                if event.alpn_protocol and not event.alpn_protocol.startswith(NODE_ALPN):
                    self.logger.error(f"Unsupported ALPN protocol: {event.alpn_protocol}")

                    return self.close(2, "Unknown ALPN.")

                if not self.peer_ed_key:
                    self.verify_cert()

            # Handle Stream Reset Event
            elif isinstance(event, (StreamReset, StopSendingReceived)):
                stream_id = event.stream_id
                error = event.error_code
                if stream_id in self.stream_buffer:
                    del self.stream_buffer[stream_id]

                self.logger.warning(
                    f"〄 Stream flushed from peer's side",
                    event_=type(event).__name__,
                    err=error,
                    stream_id=stream_id,
                )

            # Handle Connection Terminated
            elif isinstance(event, ConnectionTerminated):
                self.logger.warning(
                    "Connection terminated",
                    error_code=event.error_code,
                    frame_type=event.frame_type,
                    reason=event.reason_phrase,
                    peer=self.peer_id,
                )
                # Clean up all pending waiters to prevent "Future exception was never retrieved"
                # Note: We use set_result instead of set_exception to avoid conflicts with
                # aioquic's own exception handling. The awaiting code should check for None.
                for stream_id, waiter in list(self.waiter.items()):
                    try:
                        if not waiter.done():
                            waiter.set_result(None)
                    except Exception:
                        pass  # Ignore errors, just clean up
                    finally:
                        del self.waiter[stream_id]

            # Handle Received Data Event
            elif isinstance(event, StreamDataReceived):
                from jam.network.base.protocol_map import ProtocolMap

                # Fetch peer & data
                stream_id = event.stream_id
                data = event.data


                if not self.peer_ed_key:
                    pk = self.verify_cert()
                    if not pk:
                        self.logger.warning(
                            "Received data before TLS handshake completed, ignoring",
                            stream_id=stream_id,
                        )
                        return

                # -------------------- FIRST HANDLE THE BUFFER --------------------
                # If we don't know stream, we receive prefix
                # i.e. whenever client initiates connection or starts new protocol.
                # Add prefix to the buffer
                prefix = U8.decode(data)
                self.logger.trace(
                    f"⬇ Received data", stream_id=stream_id, prefix=prefix, data_len=len(data)
                )

                if not node:
                    self.logger.warning(
                        "Node not initialized, ignoring stream data", stream_id=stream_id
                    )
                    return

                from jam.network.protocols.up_0 import BlockAnnouncement
                UP_0 = BlockAnnouncement(jam_node)

                if (
                    self.up0_stream is None
                    # either neighbor or non validator
                    and (
                        (self.peer_ed_key in node.neighbors)
                        or (self.peer_ed_key not in state.kappa)
                    )
                    and prefix == PrefixType.UP0
                ):
                    # Send UP0 Handshake
                    UP_0.handshake(stream_id, self)
                    self.up0_stream = stream_id
                    if len(data) == 1:
                        return
                    data = data[1:]

                if self.up0_stream == event.stream_id:
                    create_safe_task(UP_0.req_intercept(stream_id, self, data), "up0 req intercept")
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
                    ce_protocol = ProtocolMap.get_protocol(prefix)(self.jam)
                    self.logger.debug(f"CE PROTOCOL TRIGGERED", p=type(ce_protocol).__name__)
                    if (stream_id in self.waiter) and (self.waiter[stream_id] is not None):
                        self.logger.debug(
                            "Intercepting Response.",
                            protocol=prefix,
                            stream_id=stream_id,
                        )
                        ce_task = create_safe_task(
                            self._handle_response(ce_protocol, stream_id), "ce res intercept"
                        )

                    else:
                        self.logger.debug(
                            "Intercepting Request.",
                            protocol=prefix,
                            stream_id=stream_id,
                        )
                        ce_task = create_safe_task(
                            self._handle_request(ce_protocol, stream_id), "ce req intercept"
                        )

                    # Clear buffer
                    ce_task.add_done_callback(lambda _: self.stream_buffer.pop(stream_id, None))

                except Exception as e:
                    # Clear waiter
                    self.logger.exception(
                        f"Error retrieving data from CE stream.",
                        error=str(e),
                        prefix=prefix,
                    )

                    if self.waiter.get(stream_id) is not None:
                        waiter = self.waiter[stream_id]
                        del self.waiter[stream_id]
                        waiter.set_result("failed to retrieve data")

                    # Clear buffer
                    self.stream_buffer.pop(stream_id, None)

        except Exception as e:
            self.logger.error(
                "Unhandled exception in quic_event_received",
                error=str(e),
                error_type=type(e).__name__,
                event_type=type(event).__name__,
            )

    async def _handle_request(self, ce_protocol: NetworkProtocol, stream_id: int):
        await ce_protocol.req_intercept(stream_id, self)

    async def _handle_response(self, ce_protocol: NetworkProtocol, stream_id: int):
        res = await ce_protocol.res_intercept(stream_id, self)

        # Wait for acknowledgment
        # Check if waiter still exists (might have been cleaned up if connection terminated)
        waiter = self.waiter.pop(stream_id, None)
        if waiter is not None and not waiter.done():
            waiter.set_result(res)

    @property
    def validator_index(self):
        state = self.jam.state
        for i, val in enumerate(state.kappa):
            if val.ed25519 == self.peer_ed_key:
                return ValidatorIndex(i)

        raise ValueError("No validator found with matching ed25519 key.")

    @property
    def val(self):
        state = self.jam.state
        validator_index = self.validator_index
        return state.kappa[validator_index]

    def get_shard_index(self, core_index: CoreIndex):
        from jam.utils.chainspec import chain_config

        vi = self.validator_index
        shard_index = ShardIndex(
            (core_index * chain_config.recovery_threshold + vi) % VALIDATOR_COUNT
        )

        return shard_index

    def sayonara(self):
        self._quic.close(error_code=0, reason_phrase="Sleep time. See you soon.")
        self.transmit()
