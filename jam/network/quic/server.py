from typing import Dict

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted
from jam.config.logging import get_logger
from jam.network.protocols.base import PrefixType

# Module-specific logger
logger = get_logger("network")

genesis_hash = "476243ad"
protocol_version = "0"

class QuicServerProtocol(QuicConnectionProtocol):
    """Quic Server Protocol for handling incoming connections from peers."""
    stream_buffer: Dict[int, bytes] = {}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._close_pending = False
        self.stream_buffer = {}
        
        # Log connection establishment
        logger.debug("QUIC server protocol initialized")

    def stream_and_close(self, stream_id: int, message: bytes) -> int:
        if self._close_pending:
            logger.warning(
                "Attempted to send on closing connection",
                stream_id=stream_id,
                message_size=len(message)
            )
            raise ConnectionError("Connection is closing")

        logger.debug(
            "Sending message with stream close",
            stream_id=stream_id,
            message_size=len(message),
            message_hex=message.hex()[:64] + "..." if len(message.hex()) > 64 else message.hex()
        )
        
        self._quic.send_stream_data(stream_id, message, end_stream=True)
        self.transmit()
        return stream_id

    def stream_and_keep_open(self, stream_id: int, message: bytes) -> int:
        if self._close_pending:
            logger.warning(
                "Attempted to send on closing connection",
                stream_id=stream_id,
                message_size=len(message)
            )
            raise ConnectionError("Connection is closing")

        logger.debug(
            "Sending message keeping stream open",
            stream_id=stream_id,
            message_size=len(message),
            message_hex=message.hex()[:64] + "..." if len(message.hex()) > 64 else message.hex()
        )
        
        self._quic.send_stream_data(stream_id, message, end_stream=False)
        self.transmit()
        return stream_id

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            # Determine peer type based on ALPN protocol
            peer_type = "unknown"
            if event.alpn_protocol == f"jamnp-s/{protocol_version}/{genesis_hash}/builder":
                peer_type = "builder"
            elif event.alpn_protocol == f"jamnp-s/{protocol_version}/{genesis_hash}":
                peer_type = "node"
            
            logger.info(
                "QUIC handshake completed",
                peer_type=peer_type,
                alpn_protocol=event.alpn_protocol,
                protocol_version=protocol_version,
                genesis_hash=genesis_hash
            )

        elif isinstance(event, ConnectionTerminated):
            logger.warning(
                "QUIC server connection terminated",
                error_code=event.error_code,
                frame_type=getattr(event, 'frame_type', None),
                reason_phrase=getattr(event, 'reason_phrase', None)
            )

        elif isinstance(event, StreamDataReceived):
            logger.debug(
                "Received stream data",
                stream_id=event.stream_id,
                data_size=len(event.data),
                end_stream=event.end_stream
            )

            # Initialize stream buffer if needed
            if event.stream_id not in self.stream_buffer:
                self.stream_buffer[event.stream_id] = bytes(0)

            self.stream_buffer[event.stream_id] += event.data

            if event.end_stream:
                self._handle_complete_stream(event.stream_id)
            else:
                self._handle_partial_stream(event)

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

            prefix = self._extract_prefix(buffer)
            
            logger.debug(
                "Processing complete stream",
                stream_id=stream_id,
                buffer_size=len(buffer),
                prefix=prefix
            )

            # Process the message
            self._process_message(buffer, stream_id, prefix)

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

    def _handle_partial_stream(self, event: StreamDataReceived):
        """Handle partial stream data (end_stream=False)"""
        try:
            buffer = event.data

            if not buffer:
                logger.warning(
                    "Received empty partial stream data",
                    stream_id=event.stream_id
                )
                return

            prefix = self._extract_prefix(buffer)
            
            # Only handle UP0 messages for partial streams
            if prefix == PrefixType.UP0:
                logger.debug(
                    "Processing UP0 message from partial stream",
                    stream_id=event.stream_id,
                    buffer_size=len(buffer)
                )
                self._process_message(buffer, event.stream_id, prefix)
            else:
                logger.debug(
                    "Ignoring non-UP0 message in partial stream",
                    stream_id=event.stream_id,
                    prefix=prefix
                )

        except Exception as e:
            logger.error(
                "Error processing partial stream",
                stream_id=event.stream_id,
                error=str(e),
                error_type=type(e).__name__
            )

    def _extract_prefix(self, buffer: bytes) -> PrefixType:
        """Extract message prefix from buffer"""
        try:
            prefix, _ = PrefixType.decodeFrom(buffer[0:1])
            return prefix
        except Exception as e:
            logger.debug(
                "Failed to extract prefix from buffer",
                buffer_size=len(buffer),
                error=str(e)
            )
            return None

    def _process_message(self, buffer: bytes, stream_id: int, prefix: PrefixType):
        """Process message with given prefix"""
        try:
            from jam.network.protocol_map import ProtocolMap

            protocol = ProtocolMap.get_protocol(prefix)()
            
            logger.debug(
                "Dispatching message to protocol handler",
                stream_id=stream_id,
                prefix=prefix,
                protocol=protocol.__class__.__name__,
                payload_size=len(buffer) - 1  # excluding prefix byte
            )
            
            protocol.server_intercept(buffer[1:], self, stream_id)
            
        except Exception as e:
            logger.error(
                "Error in protocol message processing",
                stream_id=stream_id,
                prefix=prefix,
                error=str(e),
                error_type=type(e).__name__
            )
