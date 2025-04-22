from typing import Dict

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted
from jam.config.logging import logging as logger
from typing_extensions import Optional

# from jam.network.logger.log import save_decoded_data_to_json

genesis_hash = "476243ad"
protocol_version = "0"

# QUIC Server Protocol (Handles incoming connections)
class QuicServerProtocol(QuicConnectionProtocol):
    stream_buffer: Dict[int, bytes] = {}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._close_pending = False

    def stream_and_close(self, stream_id: int, message: bytes) -> int:
        if self._close_pending:
            raise ConnectionError("Connection is closing")

        logger.info(f"📤 Sending message of size {len(message)} bytes: {message.hex()} (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)

        self.transmit()
        return stream_id

    def stream_and_keep_open(self, stream_id: int, message: bytes) -> int:
        if self._close_pending:
            raise ConnectionError("Connection is closing")

        logger.info(f"📤 Sending message of size {len(message)} bytes: {message.hex()} (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=False)

        self.transmit()
        return stream_id

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            if event.alpn_protocol == f"jamnp-s/{protocol_version}/{genesis_hash}/builder":
                print("Connected with a builder")
            elif event.alpn_protocol == f"jamnp-s/{protocol_version}/{genesis_hash}":
                print("Connected with a node")
            else:
                print("Unidentified Protocol")

            logger.info("🔗 Handshake completed.")

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Server Connection terminated: {event.error_code}")

        elif isinstance(event, StreamDataReceived):
            from jam.network.protocols.base import PrefixType
            from jam.network.protocols.ce_133 import WorkPackageSubmission

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


                    if prefix == PrefixType.CE133:
                        data = WorkPackageSubmission.intercept(buffer=buffer[1:])

                        WorkPackageSubmission.process(data=data)
                        logger.info(f"📩 Received work package : {data.package_data.work_package} with CI {data.package_data.core_index}")
                        # save_decoded_data_to_json(buffer.decode(), event.stream_id)

                    if prefix == PrefixType.CE128:
                        self.stream_and_keep_open(event.stream_id, bytes(0))

                    else:
                        try:
                            decoded_data = buffer.decode('utf-8', errors='ignore')
                            logger.warning(f"📩 Received data of size {len(buffer)} bytes")
                            # save_decoded_data_to_json(decoded_data, event.stream_id)
                            # logger.info("Saved data")

                        except UnicodeDecodeError:
                            logger.warning(
                                f"❌ Failed to decode data for stream {event.stream_id}. Saving raw data in hex.")
                            decoded_data = buffer.hex()
                            # save_decoded_data_to_json(decoded_data, event.stream_id)

                except Exception as e:
                    logger.exception(f"Error retrieving data from ce stream: {e}")

            else:
                try:
                    buffer = event.data

                    if not buffer:
                        logger.warning("📩 Received empty buffer.")
                        return

                    try:
                        prefix, _ = PrefixType.decodeFrom(buffer[0:1])
                    except Exception:
                        prefix = None

                    if prefix == PrefixType.UP0:
                        from jam.network.protocols import BlockAnnouncementProtocol

                        try:
                            announcement = BlockAnnouncementProtocol.intercept(buffer=buffer[1:])
                            logger.info(f"📩 Received block with parent: {announcement.header.parent}")
                            self.stream_buffer[event.stream_id] = bytes(0)
                            # save_decoded_data_to_json(announcement, event.stream_id)

                        except Exception as ann_err:
                            logger.warning(f"❌ Failed to parse block announcement: {ann_err}")


                except Exception as e:
                    logger.exception(f"Error retrieving data from up stream: {e}")


# QUIC Client Protocol (Initiates connections to other nodes)
class QuicClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._close_pending = False

    def stream_and_close(self, message: bytes, stream_id: Optional[int] = None) -> int:
        if self._close_pending:
            raise ConnectionError("Connection is closing")

        if stream_id is None:
            stream_id = self._quic.get_next_available_stream_id()

        logger.info(f"📤 Sending message of size {len(message)} bytes (stream {stream_id})")
        self._quic.send_stream_data(stream_id, message, end_stream=True)

        self.transmit()
        return stream_id

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
            logger.info("🔗 Handshake completed (client connected to server)")

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Client Connection terminated: {event.error_code}")
            self._close_pending = True

        elif isinstance(event, StreamDataReceived):
            response = event.data
            logger.info(f"📩 Received response: {response}")