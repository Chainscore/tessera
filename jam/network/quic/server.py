import asyncio
from typing import Dict

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted, \
    ConnectionIdIssued, ConnectionIdRetired
from cryptography.x509 import Certificate

from jam.config.logging import logging as logger
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat

genesis_hash = "476243ad"
protocol_version = "0"

class QuicServerProtocol(QuicConnectionProtocol):
    """Quic Server Protocol for handling incoming connections from peers."""
    stream_buffer: Dict[int, bytes] = {}

    def __init__(self, *args, node, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._close_pending = False
        self.stream_buffer = {}
        self.node = node

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
            peer_cert = getattr(self._quic.tls, "_peer_certificate", None)
            print("[SERVER]: peer cert", peer_cert)
            # peer_cert = self._quic.tls._peer_certificate
            #
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
            # print("server peer id", self._quic._peer_cid.cid.hex())
            # print("server host id", self._quic.host_cid.hex())
            if event.alpn_protocol == f"jamnp-s/{protocol_version}/{genesis_hash}/builder":
                print("Connected with a builder")
            elif event.alpn_protocol == f"jamnp-s/{protocol_version}/{genesis_hash}":
                print("Connected with a node")
            else:
                print("Unidentified ALPN Protocol")

            logger.info("🔗 Handshake completed.")

        elif isinstance(event, ConnectionIdIssued):
            ...
            # logger.warning(f"🔗 Connection Id issued: {event.connection_id}")
            # print("new conn id", event.connection_id.hex())

        elif isinstance(event, ConnectionIdRetired):
            ...
            # logger.warning(f"🔗 Connection Id retired: new - {event.connection_id}")
            # print("retired id", event.connection_id.hex())

        elif isinstance(event, ConnectionTerminated):
            logger.warning(f"❌ Server Connection terminated: {event.error_code}")

        elif isinstance(event, StreamDataReceived):
            from jam.network.protocols.base import PrefixType

            # h_cid = self._quic.host_cid
            # p_cid = self._quic._peer_cid

            # print("server peer id", self._quic._peer_cid.cid.hex())
            # print("server host id", self._quic.host_cid.hex())
            # san = cert.extensions.get_extension_for_oid(
            #     ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            # ).value


            # logger.info(f"data from {self._quic._peer_cid} && {self._quic.tls.certificate}")
            #             # logger.info(f"p key {self._quic.tls.certificate.public_key()} || {self._quic._peer_token}")
            #             #
            #             # public_key = self._quic.tls.certificate.public_key()
            #             # public_key_pem = public_key.public_bytes(
            #             #     encoding=Encoding.PEM,
            #             #     format=PublicFormat.SubjectPublicKeyInfo
            #             # )
            #             # print("##### key", public_key_pem)
            # peers = self.node.peers

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
                    protocol.server_intercept(self.node, buffer[1:], self, event.stream_id)

                    # Clear buffer
                    self.stream_buffer[event.stream_id] = b""

                except Exception as e:
                    # Clear buffer
                    self.stream_buffer[event.stream_id] = b""
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
                        from jam.network.protocol_map import ProtocolMap
                        protocol = ProtocolMap.get_protocol(prefix)()
                        protocol.server_intercept(self.node, buffer[1:], self, event.stream_id)


                except Exception as e:
                    logger.exception(f"Error retrieving data from up stream: {e}")
