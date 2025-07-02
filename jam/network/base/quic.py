import asyncio
from typing import Dict, Optional

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted, \
    ConnectionIdIssued, ConnectionIdRetired, StreamReset, StopSendingReceived
from cryptography.x509 import Certificate
from tsrkit_types import U8

from jam.logging import get_logger
from jam.network.base.certificate import verify_certificate
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

genesis_hash = "476243ad"
protocol_version = "0"

# Module-specific logger
logger = get_logger("network")

class QuicProtocol(QuicConnectionProtocol):
    """Quic Protocol for establishing connection with peers."""
    from jam.network.peer import Peer

    stream_buffer: Dict[int, bytes] = {}
    peer: Peer | None

    def __init__(self, *args, node, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.waiter = {}
        self.node = node
        self.peer = None
        self.peer_handshake = False
        self.stream_buffer = {}
        self._close_pending = False
        self.is_client = self._quic.configuration.is_client
        self.interface = "CLIENT" if self.is_client else "SERVER"

    def fetch_peer(self):
        """function to fetch peer in a connection"""

        if self.peer:
            return self.peer

        else:
            peer_cert = self._quic.tls._peer_certificate

            if isinstance(peer_cert, Certificate):
                # Verify certificate first
                is_valid, e = verify_certificate(peer_cert)
                if not is_valid:
                    logger.error(
                        f"❌ Invalid Peer Certificate received {e}.",
                        interface=self.interface
                    )
                    self._quic.close(error_code=0xA, reason_phrase=f"Invalid Peer Certificate")

                pk = peer_cert.public_key()
                peer = self.node.get_peer(pk.public_bytes_raw())

                if peer and peer.ed_key:
                    self.peer = peer
                    return peer
                else:
                    logger.error(
                        f"❌ Unknown peer tried to establish contact.",
                        interface=self.interface
                    )
                    self._quic.close(error_code=0x1, reason_phrase="Unknown Peer.")

            if not peer_cert:
                logger.error(
                    f"❌ No peer certificate received",
                    interface=self.interface
                )
                self._quic.close(error_code=0xA, reason_phrase="Peer's certificate not present.")

    def stream_and_keep_open(self, message: bytes, stream_id: Optional[int] = None) -> int:
        """function for streaming data without end stream (FIN) bit."""
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.debug(
            f"📤 Sending message of size {len(message)} bytes",
            stream_id=stream_id,
            interface=self.interface
        )

        self._quic.send_stream_data(stream_id, message, end_stream=False)

        self.transmit()
        return stream_id

    def stream_and_close(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        """function for streaming data with end stream (FIN) bit. used by request interceptors."""
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        logger.debug(
            f"📤 Sending message of size {len(message)} bytes.",
            stream_id=stream_id,
            interface=self.interface
        )

        self._quic.send_stream_data(stream_id, message, end_stream=True)

    async def close_and_wait(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        """function for streaming data with end stream (FIN) bit and waiting for response. used by request transmitters."""
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        logger.debug(
            f"📤 Sending message of size {len(message)} bytes.",
            stream_id = stream_id,
            interface=self.interface
        )
        self._quic.send_stream_data(stream_id, message, end_stream=True)

        try:
            waiter = self._loop.create_future()
            self.waiter[stream_id] = waiter
            self.transmit()

            logger.debug(
                "Message transmitted, waiting for response",
                stream_id=stream_id
            )
            return await asyncio.shield(waiter)

        except Exception as e:
            logger.error(
                "Error occurred while waiting for response",
                error=str(e),
                error_type=str(type(e)),
                stream_id=stream_id
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

        # Handle TLS Handshake
        if isinstance(event, HandshakeCompleted):
            # verify Certificate & fetch Peer info
            if not self.node.is_initialized:
                self.node.is_initialized = True

            peer = self.fetch_peer()
            if peer:
                logger.info(
                    f"🔗 Handshake completed with {peer}.",
                    interface=self.interface,
                    early_data=event.early_data_accepted
                )

        # elif isinstance(event, ConnectionIdIssued):
        #     logger.debug(f"🔗 Connection Id issued: {event.connection_id}",
        #     interface=self.interface
        #     )

        # elif isinstance(event, ConnectionIdRetired):
        #     logger.debug(f"🔗 Connection Id retired: {event.connection_id}",
        #     interface=self.interface
        #     )

        # Handle Stream Reset Event
        elif isinstance(event, StreamReset):
            stream_id = event.stream_id
            if stream_id in self.stream_buffer:
                del self.stream_buffer[stream_id]

            logger.warning(
                f"🔗 Stream reset.",
                error_code=event.error_code,
                interface=self.interface
            )


        # Handle Stop Sending Data Event
        elif isinstance(event, StopSendingReceived):
            stream_id = event.stream_id
            if stream_id in self.stream_buffer:
                del self.stream_buffer[stream_id]

            logger.warning(
                f"🔗 Stream reception stopped.",
                error_code=event.error_code,
                interface=self.interface
            )

        # Handle Connection Terminated Event
        elif isinstance(event, ConnectionTerminated):
            self._close_pending = True
            if self.peer in self.node.peer_conn:
                logger.debug(f"Removing {self.peer} from connections.")
                del self.node.peer_conn[self.peer]

            logger.warning(
                f"❌ Connection with {self.peer} terminated.",
                error_code=event.error_code,
                error=event.reason_phrase,
                interface=self.interface
           )

        # Handle Received Data Event
        elif isinstance(event, StreamDataReceived):
            from jam.network.base.protocol import PrefixType
            from jam.network.base.protocol_map import ProtocolMap

            # Fetch peer & data
            peer = self.fetch_peer()
            stream_id = event.stream_id
            data = event.data

            if not peer:
                raise NetworkingError(Code.NO_PEER)

            logger.debug(
                f"📩 Received data of size {len(data)} bytes.",
                peer=peer,
                stream_id=stream_id,
                interface=self.interface
            )

            # -------------------- FIRST HANDLE THE BUFFER --------------------
            # If we don't know stream, we receive prefix
            # i.e. whenever client initiates connection or starts new protocol.
            if stream_id not in self.stream_buffer:
                try:
                    # Add prefix to the buffer
                    prefix, _ = U8.decode_from(data[0:1])
                    self.stream_buffer[stream_id] = data

                    # Handle connection mapping for servers.
                    if prefix == PrefixType.UP0:
                        if not self.is_client:
                            self.node.peer_conn[peer] = (stream_id, self)
                        return

                except Exception as e:
                    prefix = None
                    logger.error(f"Error identifying protocol on unknown stream. {e}", stream_id=stream_id)

            # If we know it, then append data in the buffer
            else:
                buffer = self.stream_buffer[stream_id]
                try:
                    prefix, _ = U8.decode_from(buffer[0:1])
                    self.stream_buffer[stream_id] += data

                except Exception as e:
                    prefix = None
                    logger.error(f"Error identifying protocol on known stream. {e}")
            # -------------------- ----- ------ --- ------ --------------------


            # -------------------- THEN HANDLE THE PARSING --------------------
            # CASE: CE Streams
            if event.end_stream:
                try:
                    # Map the request to its corresponding CE protocol function
                    ce_protocol = ProtocolMap.get_protocol(prefix)()
                    if (stream_id in self.waiter) and (self.waiter[stream_id] is not None):
                        logger.debug("Intercepting Response.", protocol=prefix, stream_id=stream_id)
                        res = ce_protocol.res_intercept(stream_id, self)

                        # Wait for acknowledgment
                        waiter = self.waiter[stream_id]
                        del self.waiter[stream_id]
                        waiter.set_result(res)

                    else:
                        logger.debug("Intercepting Request.", protocol=prefix, stream_id=stream_id)
                        ce_protocol.req_intercept(stream_id, self)

                    # Clear buffer
                    self.stream_buffer.pop(stream_id, None)

                except Exception as e:
                    # Clear waiter
                    logger.exception(
                        f"Error retrieving data from ce stream.",
                        error=str(e),
                        prefix=prefix,
                        interface=self.interface
                    )

                    if self.is_client and self.waiter[stream_id] is not None:
                        waiter = self.waiter[stream_id]
                        del self.waiter[stream_id]
                        waiter.set_result("failed to retrieve data")

                    # Clear buffer
                    self.stream_buffer.pop(stream_id, None)

            # CASE: UP Streams
            else:
                if prefix == PrefixType.UP0:
                    try:
                        # Process only when receiving announcement or handshake
                        if len(data) == 4:
                            return
                        up_protocol = ProtocolMap.get_protocol(prefix)()
                        up_protocol.req_intercept(stream_id, self)

                    except Exception as e:
                        # Clear buffer
                        logger.exception(
                            f"Error retrieving data from up stream.",
                            error=str(e),
                            prefix=prefix,
                            interface=self.interface
                        )
                        self.stream_buffer[stream_id] = prefix.encode()
            # -------------------- ----- ------ --- ------ --------------------
