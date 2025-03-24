import asyncio
from typing import Dict, Optional

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.connection import logger
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted

from jam.types.block import Block


# QUIC Server Protocol (Handles incoming connections)
class QuicServerProtocol(QuicConnectionProtocol):
    stream_buffer: Dict[int, bytes] = {}

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            logger.info(f"🔗 Handshake completed with {self._quic.configuration.is_client}")

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Server Connection terminated: {event.error_code}")

        elif isinstance(event, StreamDataReceived):
            logger.info(f"📩 Received data of size {len(event.data)} bytes {event}")
            if event.stream_id not in self.stream_buffer:
                self.stream_buffer[event.stream_id] = bytes(0)
            
            self.stream_buffer[event.stream_id] += event.data
            if event.end_stream:
                try:
                    message = Block.decode_from(self.stream_buffer[event.stream_id])
                    logger.info(f"📩 Received block: {message}")
                except Exception as e:
                    message = self.stream_buffer[event.stream_id].decode()
                    logger.warning(f"📩 Received message: {message}")


# QUIC Client Protocol (Initiates connections to other nodes)
class QuicClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._close_pending = False

    async def send_message(self, message: bytes):
        if self._close_pending:
            raise ConnectionError("Connection is closing")
            
        stream_id = self._quic.get_next_available_stream_id()
        logger.info(f"📤 Sending message of size {len(message)} bytes: {message.hex()} (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)
        self.transmit()

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, HandshakeCompleted):
            logger.info("🔗 Handshake completed (client connected to server)")

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Client Connection terminated: {event.error_code}")
            self._close_pending = True

        elif isinstance(event, StreamDataReceived):
            response = event.data
            logger.info(f"📩 Received response: {response}")