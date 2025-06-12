import asyncio
from typing import Dict, Optional

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted, \
    ConnectionIdIssued, ConnectionIdRetired, StreamReset, StopSendingReceived
from cryptography.x509 import Certificate

from jam.config.logging import logging as logger
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

genesis_hash = "476243ad"
protocol_version = "0"

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
        if self.peer:
            return self.peer

        else:
            peer_cert = self._quic.tls._peer_certificate

            if isinstance(peer_cert, Certificate):
                pk = peer_cert.public_key()
                peer = self.node.get_peer(pk.public_bytes_raw())
                if peer:
                    self.peer = peer
                    return peer
                else:
                    logger.error(f"{self.interface}: ❌ Unknown peer tried to establish contact.")
                    self._quic.close(error_code=0x1, reason_phrase="Unknown Peer.")

            if not peer_cert:
                logger.error(f"{self.interface}: ❌ No peer certificate received")
                self._quic.close(error_code=0xA, reason_phrase="Peer's certificate not present.")

    def stream_and_close(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        logger.info(f"{self.interface}: 📤 Sending message of size {len(message)} bytes (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)

    async def close_and_wait(self, message: bytes, stream_id: int, timeout: Optional[float] = 2.0):
        """stream and close function for clients"""

        if self._close_pending:
            raise ConnectionError("Connection is closing.")

        logger.info(f"{self.interface}: 📤 Sending message of size {len(message)} bytes (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)

        if self.is_client:
            waiter = self._loop.create_future()
            self.waiter[stream_id] = waiter
            self.transmit()
            return await asyncio.shield(waiter)

            # try:
            #     return await asyncio.wait_for(asyncio.shield(waiter), timeout=timeout)
            # except asyncio.TimeoutError:
            #     logger.warning(f"⏱️ Timeout waiting for stream {stream_id} response")
            #     del self.waiter[stream_id]
            #     return None

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
            # verify Certificate & fetch Peer info
            peer = self.fetch_peer()
            if peer:
                logger.info(f"{self.interface}: 🔗 Handshake completed with {peer}.")

        elif isinstance(event, ConnectionIdIssued):
            logger.info(f"{self.interface}: 🔗 Connection Id issued: {event.connection_id}")

        elif isinstance(event, ConnectionIdRetired):
            logger.warning(f"{self.interface}: 🔗 Connection Id retired: {event.connection_id}")

        elif isinstance(event, StreamReset):
            stream_id = event.stream_id
            if stream_id in self.stream_buffer:
                del self.stream_buffer[stream_id]

            logger.warning(f"{self.interface}: 🔗 Stream reset: {stream_id}. Error: {event.error_code}.")

        elif isinstance(event, StopSendingReceived):
            stream_id = event.stream_id
            if stream_id in self.stream_buffer:
                del self.stream_buffer[stream_id]

            logger.warning(f"{self.interface}: 🔗 Stream Reception Stopped: {stream_id}. Error: {event.error_code}.")

        elif isinstance(event, ConnectionTerminated):
            self._close_pending = True
            logger.warning(f"{self.interface}: ❌ Connection with {self.peer} terminated: {event.error_code}. Reason: {event.reason_phrase}.")

        elif isinstance(event, StreamDataReceived):
            from jam.network.protocols.base import PrefixType
            from jam.network.base.protocol_map import ProtocolMap


            stream_id = event.stream_id
            data = event.data

            logger.info(f"{self.interface}: 📩 Received data of size {len(data)} bytes on stream {stream_id}")
            peer = self.fetch_peer()
            if not peer:
                raise NetworkingError(Code.NO_PEER)

            logger.info(f"{self.interface}: 🔗 Found {peer}.")
            print(f"{self.interface}: peer address", self._quic._network_paths[0].addr)

            prefix = None

            # If we don't know stream, we receive prefix i.e. whenever client initiates connection.
            if stream_id not in self.stream_buffer:
                try:
                    prefix, _ = PrefixType.decodeFrom(data[0:1])
                    self.stream_buffer[stream_id] = data
                    if prefix == PrefixType.UP0:
                        if not self.is_client:
                            self.node.peer_conn[peer] = (stream_id, self)
                        return

                except Exception:
                    prefix = None

            # If we know it, then append data
            else:
                buffer = self.stream_buffer[stream_id]
                try:
                    prefix, _ = PrefixType.decodeFrom(data[0:1])
                    self.stream_buffer[stream_id] = data
                    if prefix == PrefixType.UP0:
                        if not self.is_client:
                            self.node.peer_conn[peer] = (stream_id, self)
                        return

                except Exception:
                    prefix = None
                buffer += data

            if event.end_stream:
                try:
                    # Map the request to its corresponding CE protocol function
                    ce_protocol = ProtocolMap.get_protocol(prefix)()

                    if self.is_client & self.waiter[stream_id] is not None:
                        data = ce_protocol.res_intercept(stream_id, self)

                        # Wait for acknowledgment
                        waiter = self.waiter[stream_id]
                        del self.waiter[stream_id]
                        waiter.set_result(data)

                    elif not self.is_client:
                        ce_protocol.req_intercept(stream_id, self)

                    # Clear buffer
                    del self.stream_buffer[stream_id]

                except Exception as e:
                    # Clear waiter
                    if self.is_client and self.waiter[stream_id] is not None:
                        waiter = self.waiter[stream_id]
                        del self.waiter[stream_id]
                        waiter.set_result("failed to retrieve data")

                    # Clear buffer
                    self.stream_buffer.pop(stream_id, None)
                    logger.exception(f"{self.interface}: Error retrieving data from ce stream: {e}")

            else:
                if prefix == PrefixType.UP0:
                    try:
                        up_protocol = ProtocolMap.get_protocol(prefix)()
                        up_protocol.req_intercept(stream_id, self)
                    except Exception as e:
                        # Clear buffer
                        self.stream_buffer[stream_id] = prefix.encode()
                        logger.exception(f"{self.interface}: Error retrieving data from up stream: {e}")