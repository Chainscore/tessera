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
            print(f"🔗 Handshake completed with {self._quic.configuration.is_client}")

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Server Connection terminated: {event.error_code}")

        elif isinstance(event, StreamDataReceived):
            print(f"📩 Received data of size {len(event.data)} bytes {event}")
            if event.stream_id not in self.stream_buffer:
                self.stream_buffer[event.stream_id] = bytes(0)
            
            self.stream_buffer[event.stream_id] += event.data
            if event.end_stream:
                try:
                    message = Block.decode_from(self.stream_buffer[event.stream_id])
                    print(f"📩 Received block: {message}")
                except Exception as e:
                    message = self.stream_buffer[event.stream_id].decode()
                    print(f"📩 Received message: {message}")


# QUIC Client Protocol (Initiates connections to other nodes)
class QuicClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ack_waiter: Optional[asyncio.Future[str]] = None
        self._close_pending = False

    async def send_message(self, message: bytes) -> str:
        if self._close_pending:
            raise ConnectionError("Connection is closing")
            
        stream_id = self._quic.get_next_available_stream_id()
        print(f"📤 Sending message of size {len(message)} bytes: {message.hex()} (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)
        self.transmit()

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, HandshakeCompleted):
            print("🔗 Handshake completed (client connected to server)")

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Client Connection terminated: {event.error_code}")
            self._close_pending = True
            # If there's a pending ack waiter, complete it with error
            # if self._ack_waiter and not self._ack_waiter.done():
            #     self._ack_waiter.set_exception(ConnectionError("Connection terminated"))

        elif isinstance(event, StreamDataReceived) and self._ack_waiter:
            response = event.data
            print(f"📩 Received response: {response}")
            # if not self._ack_waiter.done():
            #     self._ack_waiter.set_result(response)
            # self._ack_waiter = None
            # response = "Echo".encode()
            # print(f"📤 Sending response: {response.decode()}")
            # self._quic.send_stream_data(event.stream_id, response, end_stream=False)