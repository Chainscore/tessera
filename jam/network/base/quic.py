import asyncio
from typing import Dict, Optional

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted, \
    ConnectionIdIssued, ConnectionIdRetired
from cryptography.x509 import Certificate

from jam.config.logging import logging as logger

genesis_hash = "476243ad"
protocol_version = "0"

class QuicProtocol(QuicConnectionProtocol):
    """Quic Protocol for establishing connection with peers."""
    stream_buffer: Dict[int, bytes] = {}

    def __init__(self, *args, node, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.waiter = {}
        self.node = node
        self.peer = None
        self.stream_buffer = {}
        self._close_pending = False
        self.is_client = self._quic.configuration.is_client
        self.interface = "CLIENT" if self.is_client else "SERVER" 

    async def stream_and_close(self, message: bytes, stream_id: Optional[int] = None):
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.info(f"{self.interface}: 📤 Sending message of size {len(message)} bytes (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)
        
        if self.is_client:
            waiter = self._loop.create_future()
            self.waiter[stream_id] = waiter
            self.transmit()
            return await asyncio.shield(waiter)


    def stream_and_keep_open(self, message: bytes, stream_id: Optional[int] = None) -> int:
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.info(f"{self.interface}: 📤 Sending message of size {len(message)} bytes. (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=False)

        self.transmit()
        return stream_id


    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, HandshakeCompleted):
            # Fetch & Verify Certificate
            peer_cert = self._quic.tls._peer_certificate

            if isinstance(peer_cert, Certificate):
                pk = peer_cert.public_key()
                peer = self.node.get_peer(pk)
                if peer:
                    self.peer = peer
                    if not self.is_client:
                        self.node.peer_conn[peer] = (-1, self)
                    logger.info(f"{self.interface}: 🔗 Handshake completed with {peer}.")
                else:
                    logger.error(f"{self.interface}: ❌ Unknown peer tried to establish contact.")
                    self._quic.close(error_code=0x1, reason_phrase="No trespassing allowed on secured parameters.")
            
            if not peer_cert:
                logger.error(f"{self.interface}: ❌ No peer certificate received")
                self._quic.close(error_code=0xA, reason_phrase="Peer's certificate not present.")

        elif isinstance(event, ConnectionIdIssued):
            logger.info(f"{self.interface}: 🔗 Connection Id issued: {event.connection_id}")

        elif isinstance(event, ConnectionIdRetired):
            logger.warning(f"{self.interface}: 🔗 Connection Id retired: {event.connection_id}")

        elif isinstance(event, ConnectionTerminated):
            self._close_pending = True
            logger.warning(f"{self.interface}: ❌ Connection with peer {self.peer} terminated: {event.error_code}. Reason: {event.reason_phrase}.")

        elif isinstance(event, StreamDataReceived):
            stream_id = event.stream_id
            data = event.data

            # Check Which

            if not self.peer:
                peer_cert = self._quic.tls._peer_certificate

                if isinstance(peer_cert, Certificate):
                    pk = peer_cert.public_key()
                    peer = self.node.get_peer(pk)

                    if peer:
                        self.peer = peer
                        if not self.is_client:
                            self.node.peer_conn[peer] = (stream_id, self)
                        logger.info(f"{self.interface}: 🔗 Handshake completed with {peer}.")
                    else:
                        logger.error(f"{self.interface}: ❌ Unknown peer tried to establish contact.")
                        self._quic.close(error_code=0x1, reason_phrase="No trespassing allowed on secured parameters.")

                if not peer_cert:
                    logger.error(f"{self.interface}: ❌ No peer certificate received")
                    self._quic.close(error_code=0xA, reason_phrase="Peer's certificate not present.")

            logger.info(f"{self.interface}: 📩 Received data of size {len(data)} bytes on stream {stream_id}")

            if stream_id not in self.stream_buffer:
                self.stream_buffer[stream_id] = b""

            self.stream_buffer[stream_id] += data
            
            from jam.network.protocols.base import PrefixType
            from jam.network.protocol_map import ProtocolMap

            buffer = self.stream_buffer[stream_id]

            if not buffer:
                logger.warning(f"{self.interface}: 📩 Received empty buffer.")
                return
            
            if event.end_stream:
                # Handle CE Streams

                try:
                    try:
                        prefix, _ = PrefixType.decodeFrom(buffer[0:1])
                    except Exception:
                        prefix = None

                    # Map the request to its corresponding protocol function
                    protocol = ProtocolMap.get_protocol(prefix)()

                    if self.is_client & self.waiter[stream_id] is not None:
                        data = protocol.client_intercept(self.node, buffer[1:], stream_id)

                        # Wait for acknowledgment
                        waiter = self.waiter[stream_id]
                        self.waiter[stream_id] = None
                        waiter.set_result(data)

                    elif not self.is_client:
                        protocol.server_intercept(self.node, buffer[1:], self, stream_id)

                    # Clear buffer
                    self.stream_buffer[stream_id] = b""

                except Exception as e:

                    # Clear waiter
                    if self.is_client & self.waiter[stream_id] is not None:
                        waiter = self.waiter[stream_id]
                        self.waiter[stream_id] = None
                        waiter.set_result("failed to retrieve data")

                    # Clear buffer
                    self.stream_buffer[stream_id] = b""
                    logger.exception(f"{self.interface}: Error retrieving data from ce stream: {e}")
            
            else:
                # Handle UP Streams
                try:
                    try:
                        prefix, _ = PrefixType.decodeFrom(buffer[0:1])
                    except Exception:
                        prefix = None

                    if prefix == PrefixType.UP0:
                        if self.peer:
                            if self.peer in self.node.peer_conn:
                                up_stream, conn = self.node.peer_conn[self.peer]

                                if up_stream == -1:
                                    self.node.peer_conn[self.peer][0] = stream_id

                                elif up_stream != stream_id:
                                    logger.error(f"{self.interface}: ❌ Different UP Stream.")
                                    self._quic.close(error_code=0x4, reason_phrase="Multiple UP streams are no.")
                                    return

                        protocol = ProtocolMap.get_protocol(prefix)()
                        protocol.server_intercept(buffer[1:], stream_id, self)
                        
                    # Clear buffer
                    self.stream_buffer[stream_id] = b""

                except Exception as e:
                    # Clear buffer
                    self.stream_buffer[stream_id] = b""
                    logger.exception(f"{self.interface}: Error retrieving data from up stream: {e}")



