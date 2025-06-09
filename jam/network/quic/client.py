from typing import Dict, Optional

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted
from jam.config.logging import get_logger

# Module-specific logger
logger = get_logger("network")

genesis_hash = "476243ad"
protocol_version = "0"

class QuicClientProtocol(QuicConnectionProtocol):
    """Quic Client Protocol for initiating connections to peers."""
    stream_buffer: Dict[int, bytes] = {}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._close_pending = False
        self.stream_buffer = {}
        
        logger.debug("Networking: Client protocol initialized")

    def stream_and_close(self, message: bytes, stream_id: Optional[int] = None) -> int:
        if self._close_pending:
            logger.warning(
                "Attempted to send message on closing connection",
                stream_id=stream_id,
                message_size=len(message)
            )
            raise ConnectionError("Connection is closing")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.debug(
            "Sending message with stream close",
            stream_id=stream_id,
            message_size=len(message),
            message_hex=message.hex()[:64] + "..." if len(message.hex()) > 64 else message.hex()
        )
        
        self._quic.send_stream_data(stream_id, message, end_stream=True)
        self.transmit()
        return stream_id

    def stream_and_keep_open(self, message: bytes, stream_id: Optional[int] = None) -> int:
        if self._close_pending:
            logger.warning(
                "Attempted to send message on closing connection",
                stream_id=stream_id,
                message_size=len(message)
            )
            raise ConnectionError("Connection is closing")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.debug(
            "Sending message keeping stream open",
            stream_id=stream_id,
            message_size=len(message),
            message_hex=message.hex()[:64] + "..." if len(message.hex()) > 64 else message.hex()
        )
        
        self._quic.send_stream_data(stream_id, message, end_stream=False)
        self.transmit()
        return stream_id

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, HandshakeCompleted):
            logger.info(
                "QUIC client handshake completed",
                alpn_protocol=event.alpn_protocol,
                protocol_version=protocol_version,
                genesis_hash=genesis_hash
            )

        elif isinstance(event, ConnectionTerminated):
            logger.warning(
                "QUIC client connection terminated",
                error_code=event.error_code,
                frame_type=getattr(event, 'frame_type', None),
                reason_phrase=getattr(event, 'reason_phrase', None)
            )
            self._close_pending = True

        elif isinstance(event, StreamDataReceived):
            logger.debug(
                "Received stream data",
                stream_id=event.stream_id,
                data_size=len(event.data),
                end_stream=event.end_stream
            )

            if event.stream_id not in self.stream_buffer:
                self.stream_buffer[event.stream_id] = bytes(0)

            self.stream_buffer[event.stream_id] += event.data

            if event.end_stream:
                self._handle_complete_stream(event.stream_id)

    def _handle_complete_stream(self, stream_id: int):
        """Handle a complete stream (end_stream=True)"""
        try:
            buffer = self.stream_buffer[stream_id]

            if not buffer:
                logger.warning(
                    "Received empty stream buffer",
                    stream_id=stream_id
                )
                return

            try:
                from jam.network.protocols.base import PrefixType
                prefix, _ = PrefixType.decodeFrom(buffer[0:1])
            except Exception as e:
                logger.warning(
                    "Failed to decode message prefix",
                    stream_id=stream_id,
                    buffer_size=len(buffer),
                    error=str(e)
                )
                prefix = None

            logger.debug(
                "Processing complete stream",
                stream_id=stream_id,
                buffer_size=len(buffer),
                prefix=prefix
            )

            # Map the request to its corresponding protocol function
            from jam.network.protocol_map import ProtocolMap

            try:
                protocol = ProtocolMap.get_protocol(prefix)()
                protocol.client_intercept(buffer[1:], stream_id)
                
                logger.debug(
                    "Message processed by protocol handler",
                    stream_id=stream_id,
                    protocol=protocol.__class__.__name__,
                    prefix=prefix
                )
            except Exception as e:
                logger.error(
                    "Error in protocol message processing",
                    stream_id=stream_id,
                    prefix=prefix,
                    error=str(e),
                    error_type=type(e).__name__
                )

            # Clear buffer
            self.stream_buffer[stream_id] = b""

        except Exception as e:
            # Clear buffer on error
            self.stream_buffer[stream_id] = b""
            logger.error(
                "Error processing complete stream",
                stream_id=stream_id,
                error=str(e),
                error_type=type(e).__name__
            )