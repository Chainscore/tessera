import ssl
import socket
import asyncio
from typing import Optional

from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.logger import QuicLogger

from jam.log_setup import node_logger as logger
from jam.network.base.certificate import generate_keys
from jam.network.base.sessions import SessionTicketStore
from jam.network.connection import NodeConnection
from jam.network.node import QuicNode
from jam.utils.constants import NODE_ALPN
from jam.config import NodeConfig

class NetworkService:
    def __init__(self, config: NodeConfig):
        self.config = config
        self.node: Optional[QuicNode] = None
        self._transport = None
        
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
            logger.warning("SO_REUSEPORT not supported on this platform, continuing without it")
        
        try:
            sock.bind((self.config.HOST, self.config.PORT))
        except OSError as e:
            logger.error(f"Failed to bind to {self.config.HOST}:{self.config.PORT}: {e}")
            raise

        # --- Keys --- #
        print(f"DEBUG: Generating keys for port {self.config.PORT}...")
        san = generate_keys(self.config.PORT)
        print(f"DEBUG: Keys generated.")
        
        # --- QUIC Configuration --- #
        cfg = QuicConfiguration(
            is_client=True,
            verify_mode=ssl.CERT_NONE, 
            max_data=(100*1024*1024), 
            max_stream_data=(10*1024*1024), 
            max_datagram_size=1350, 
            idle_timeout=600
        )
        cfg.quic_logger = QuicLogger()
        cfg.load_cert_chain(f"seeds/{self.config.PORT}/cert.pem", f"seeds/{self.config.PORT}/key.pem")
        cfg.alpn_protocols = [NODE_ALPN] 
        if self.config.BUILDER:
            cfg.alpn_protocols[0] += ("/builder")

        # --- Session Ticket Store --- #
        session_ticket_store = SessionTicketStore(self.config.PORT)

        # --- Start Peer --- #
        print(f"DEBUG: Creating datagram endpoint...")
        self._transport, proto = await loop.create_datagram_endpoint(
            lambda: QuicNode(
                _id=san,
                cfg=cfg,
                create_protocol=lambda *args, **kwargs: NodeConnection(*args, **kwargs),
                session_ticket_fetcher=session_ticket_store.pop,
                session_ticket_handler=session_ticket_store.add,
                retry=False,
                stream_handler=None,
            ),
            sock=sock
        )

        # proto.set_neighbors() # Removed: depends on state
        proto.port = self.config.PORT
        self.node = proto

        logger.info(f"Initialized NetworkService", id=san, host=self.config.HOST, port=self.config.PORT)
        return self.node

    async def connect_to_peers(self, state, settings):
        """Connect to peers based on current state and settings."""
        if not self.node:
            logger.warning("NetworkService not started, cannot connect to peers.")
            return

        # Inject dependencies
        self.node.state = state
        self.node.settings = settings
        self.node.set_neighbors(state, settings) # Now we have state and settings

        index = settings.validator_index
        peers = set(state.kappa)
        
        # Optimization: connect to neighbors in shuffle
        if index is not None: # Check if we are a validator
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
            if peer.metadata.port == self.config.PORT:
                continue
            tasks.append(asyncio.create_task(self.node.connect(peer)))
        
        if tasks:
            await asyncio.gather(*tasks)

    def stop(self):
        if self._transport:
            logger.info("Closing network transport...")
            self._transport.close()
            self._transport = None
            logger.info("Network transport closed.")
