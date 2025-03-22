import asyncio
from typing import Optional

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.connection import logger
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted


# QUIC Server Protocol (Handles incoming connections)
class QuicServerProtocol(QuicConnectionProtocol):
    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            print(f"🔗 Handshake completed with {self._quic.configuration.is_client}")

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Server Connection terminated: {event.error_code}")

        elif isinstance(event, StreamDataReceived):
            message = event.data.decode()
            print(f"📩 Received message: {message}")

            # Send response back
            # response = f"Echo: {message}".encode()
            # print(f"📤 Sending response: {response.decode()}")
            # self._quic.send_stream_data(event.stream_id, response, end_stream=False)


# QUIC Client Protocol (Initiates connections to other nodes)
class QuicClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ack_waiter: Optional[asyncio.Future[str]] = None
        self._close_pending = False

    async def send_message(self, message: str) -> str:
        if self._close_pending:
            raise ConnectionError("Connection is closing")
            
        stream_id = self._quic.get_next_available_stream_id()
        print(f"📤 Sending message: {message} (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message.encode(), end_stream=True)

        # waiter = self._loop.create_future()
        # self._ack_waiter = waiter
        self.transmit()
        # return await asyncio.shield(waiter)

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
            response = event.data.decode()
            print(f"📩 Received response: {response}")
            # if not self._ack_waiter.done():
            #     self._ack_waiter.set_result(response)
            # self._ack_waiter = None
            # response = "Echo".encode()
            # print(f"📤 Sending response: {response.decode()}")
            # self._quic.send_stream_data(event.stream_id, response, end_stream=False)