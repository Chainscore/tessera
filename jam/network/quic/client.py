import asyncio
from typing import Dict, Optional

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted, \
    ConnectionIdIssued, ConnectionIdRetired
from cryptography.x509 import Certificate

from jam.config.logging import logging as logger

genesis_hash = "476243ad"
protocol_version = "0"

class QuicClientProtocol(QuicConnectionProtocol):
    """Quic Client Protocol for initiating connections to peers."""
    stream_buffer: Dict[int, bytes] = {}

    def __init__(self, *args, node, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._close_pending = False
        self.stream_buffer = {}
        self.waiter = {}
        self.connection_id = 0
        self.node = node

    async def stream_and_close(self, message: bytes, stream_id: Optional[int] = None):
        if self._close_pending:
            raise ConnectionError("Connection is closing")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.info(f"📤 Sending message of size {len(message)} bytes (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)

        waiter = self._loop.create_future()
        self.waiter[stream_id] = waiter
        self.transmit()
        return await asyncio.shield(waiter)

    def stream_and_keep_open(self, message: bytes, stream_id: Optional[int] = None) -> int:
        if self._close_pending:
            raise ConnectionError("Connection is closing")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.info(f"📤 Sending message of size {len(message)} bytes. (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=False)

        self.transmit()
        return stream_id


    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, HandshakeCompleted):
            peer_cert = self._quic.tls._peer_certificate
            print("[CLIENT]: peer cert", peer_cert)
            #
            # if isinstance(peer_cert, Certificate):
            #     pk = peer_cert.public_key()
            #     print("pk", pk)
            #     peer = self.node.get_peer_from_pub(pk)
            #     if peer:
            #         print("found peer", peer)
            #
            # if not peer_cert:
            #     print("❌ No peer certificate received")
            #     self._quic.close(error_code=0x10, reason_phrase="No cert")
            #     return
            #
            # print("peer certificate", peer_cert)
            # print("client peer id", self._quic._peer_cid.cid.hex())
            # print("client host id", self._quic.host_cid.hex())

            logger.info("🔗 Handshake completed (client connected to server)")

        elif isinstance(event, ConnectionIdIssued):
            ...
            # logger.warning(f"🔗 Connection Id issued: {event.connection_id}")
            # self.connection_id = event.connection_id
            # print("new conn id", event.connection_id.hex())

        elif isinstance(event, ConnectionIdRetired):
            ...
            # logger.warning(f"🔗 Connection Id retired: new - {event.connection_id}")
            # print("retired id", event.connection_id.hex())


        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Client Connection terminated: {event.error_code}")
            self._close_pending = True

        elif isinstance(event, StreamDataReceived):
            # print("client peer id", self._quic._peer_cid.cid.hex())
            # print("client host id", self._quic.host_cid.hex())

            if self.waiter[event.stream_id] is not None:
                from jam.network.protocols.base import PrefixType

                logger.info(f"📩 Received data of size {len(event.data)} bytes on stream {event.stream_id}")

                if event.stream_id not in self.stream_buffer:
                    self.stream_buffer[event.stream_id] = bytes(0)

                self.stream_buffer[event.stream_id] += event.data

                if event.end_stream:
                    try:
                        buffer = self.stream_buffer[event.stream_id]

                        if not buffer:
                            logger.warning("📩 Received empty buffer.")
                            return

                        try:
                            prefix, _ = PrefixType.decodeFrom(buffer[0:1])
                        except Exception:
                            prefix = None

                        # Map the request to its corresponding protocol function
                        from jam.network.protocol_map import ProtocolMap

                        protocol = ProtocolMap.get_protocol(prefix)()
                        data = protocol.client_intercept(self.node ,buffer[1:], event.stream_id)

                        # Wait for acknowledgment
                        waiter = self.waiter[event.stream_id]
                        self.waiter[event.stream_id] = None
                        waiter.set_result(data)

                        # Clear buffer
                        self.stream_buffer[event.stream_id] = b""

                    except Exception as e:

                        waiter = self.waiter[event.stream_id]
                        self.waiter[event.stream_id] = None
                        waiter.set_result("failed to retrieve data")

                        # Clear buffer
                        self.stream_buffer[event.stream_id] = b""
                        logger.exception(f"Error retrieving data from ce stream: {e}")