import ssl
import socket
import asyncio
import structlog
from typing import Optional, TYPE_CHECKING, Any

from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.logger import QuicLogger

from jam.network.base.certificate import generate_keys
from jam.network.base.protocol import U8
from jam.network.base.protocol_map import ProtocolMap
from jam.network.base.sessions import SessionTicketStore
from jam.network.connection import PeerConnection
from jam.network.node import QuicNode
from jam.utils.constants import NODE_ALPN, BUILDER_ALPN
from jam.utils.gather import gather_with_exceptions
from jam.utils.task_utils import create_safe_task

if TYPE_CHECKING:
    from jam.jam_node import JamNode
    from jam.settings import Settings
    from jam.state.state import State


class NetworkService:
    def __init__(self, jam_node: "JamNode"):
        self.jam = jam_node
        self._node: Optional[QuicNode] = None
        self._transport = None
        self.logger = structlog.get_logger("network")

    @property
    def node(self) -> QuicNode:
        if self._node is None:
            raise RuntimeError("Network Endpoint is not initialized!")
        return self._node

    @property
    def state(self) -> "State":
        return self.jam.state

    @property
    def settings(self) -> "Settings":
        return self.jam.settings

    @node.setter
    def node(self, value: QuicNode) -> None:
        self._node = value

    async def start(self) -> QuicNode:
        """
        Start the QUIC node service.
        """
        loop = asyncio.get_running_loop()

        # --- Socket --- #
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            self.logger.warning(
                "SO_REUSEPORT not supported on this platform, continuing without it"
            )

        config = self.jam.config

        try:
            sock.bind((config.HOST, config.PORT))
        except OSError as e:
            self.logger.error(
                f"Failed to bind to {config.HOST}:{config.PORT}: {e}"
            )
            raise

        # --- Keys --- #
        san = generate_keys(self.settings)

        # --- QUIC Configuration --- #
        cfg = QuicConfiguration(
            is_client=True,
            verify_mode=ssl.CERT_NONE,
            max_data=(100 * 1024 * 1024),
            max_stream_data=(10 * 1024 * 1024),
            max_datagram_size=1350,
            idle_timeout=600,
        )
        cfg.quic_logger = QuicLogger()
        cfg.load_cert_chain(
            f"seeds/{config.PORT}/cert.pem", f"seeds/{config.PORT}/key.pem"
        )
        cfg.alpn_protocols = [NODE_ALPN, BUILDER_ALPN]

        # --- Session Ticket Store --- #
        session_ticket_store = SessionTicketStore(config.PORT)

        # --- Start Peer --- #
        self.logger.trace("Creating datagram endpoint.")
        self._transport, proto = await loop.create_datagram_endpoint(
            lambda: QuicNode(
                _id=san,
                jam=self.jam,
                cfg=cfg,
                create_protocol=lambda *args, **kwargs: PeerConnection(
                    *args, jam_node=self.jam, **kwargs
                ),
                session_ticket_fetcher=session_ticket_store.pop,
                session_ticket_handler=session_ticket_store.add,
                retry=False,
                stream_handler=None,
            ),
            sock=sock,
        )

        # proto.set_neighbors() # Removed: depends on state
        proto.port = config.PORT
        self.node = proto

        self.logger.info(
            f"Initialized NetworkService",
            id=san,
            host=config.HOST,
            port=config.PORT,
        )
        return self.node

    async def dispatch(self, prefix: int, data: Any, *args, **kwargs):
        """
        Dispatches transmit call for specific protocol
        """
        protocol = ProtocolMap.get_protocol(U8(prefix))(self.jam)
        res = await protocol.transmit(data, *args, **kwargs)

        return res

    async def connect_to_peers(self):
        """Connect to peers based on current state and settings."""
        if not self.node:
            self.logger.warning("NetworkService not started, cannot connect to peers.")
            return

        state = self.state
        settings = self.settings

        # Inject dependencies
        # TODO: Do we need manual injection here?
        # self.node.state = state
        # self.node.settings = settings
        self.node.set_neighbors()

        index = settings.validator_index(state)
        peers = set(state.kappa)

        # Optimization: connect to neighbors in shuffle
        if index is not None:  # Check if we are a validator
            # This logic mimics the original start.py logic but needs safety if index is not valid
            # Assuming val_index logic in settings handles the 'None' case or we check it here
            try:
                # TODO: Verify this logic matches Graypaper/original implementation intent
                if index < len(state.lambda_) and index < len(state.iota):
                    peers.add(state.lambda_[index])
                    # peers.add(state.gamma.p[index]) # Gamma might be structured differently
                    peers.add(state.iota[index])
            except IndexError:
                pass

        tasks = []
        for peer in peers:
            if peer.metadata.port == self.jam.config.PORT:
                continue

            if not (
                    (peer.ed25519[31] > 127)
                    ^ (settings.ed25519_public[31] > 127)
                    ^ (int.from_bytes(peer.ed25519) < int.from_bytes(settings.ed25519_public))
            ):
                print("CONNECTING TO", peer)

            tasks.append(create_safe_task(self.node.connect(peer, self.jam)))

        if tasks:
            await gather_with_exceptions(tasks)

    def stop(self):
        if self._node:
            self.logger.trace("Closing connections...")
            self._node.close()
            self.logger.info("Peer Connections closed.")

        if self._transport:
            self.logger.trace("Closing network transport...")
            self._transport.close()
            self._transport = None
            self.logger.info("Network transport closed.")
