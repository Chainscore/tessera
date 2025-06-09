import asyncio
import json
import ssl
from typing import Dict, cast, Tuple

from aioquic.asyncio import serve, connect
from aioquic.asyncio.server import QuicServer
from aioquic.quic.configuration import QuicConfiguration
from jam.config.logging import get_logger
from jam.types.protocol.validators import ValidatorData
from .certificate import generate_keys
from .peer import Peer
from .quic.client import QuicClientProtocol
from .quic.server import QuicServerProtocol
from .sessions import SessionTicketStore

logger = get_logger("network")

genesis_hash = "476243ad"
protocol_version = "0"

class Node:
    """
    Represents a node in the network.
    Args:
        node_id (str): Id of the node
        node_name (str): Name of the node
        host (str): Host address
        port (int): Running port of the node
        validator_data (ValidatorData): Public keys and metadata of the node
        peers (list[Peer]): List of all the peers of the node.
    """
    __id: str
    name: str
    host: str
    port: int
    validator_data: ValidatorData
    seed: bytes

    peers: list[Peer]

    dns: str
    server: QuicServer

    is_initialized: bool = False
    is_builder: bool = False
    is_validator: bool = True

    # state: State

    peer_conn: Dict[Peer, Tuple[int, QuicClientProtocol]] = {}
    connections: list[QuicClientProtocol] = []

    def __init__(self, node_id: str, node_name: str, host: str, port: int, validator_data, peers: list[Peer], is_builder: bool, is_validator: bool):
        self.__id = node_id
        self.name = node_name
        self.host = host
        self.port = port
        self.validator_data = validator_data
        self.peers = peers
        self.is_builder = is_builder
        self.is_validator = is_validator
        self.connections = []
        self.peer_conn = {}

        if is_validator and is_builder:
            logger.error(
                "Invalid node configuration - cannot be both validator and builder",
                node_id=node_id,
                node_name=node_name,
                host=host,
                port=port
            )
            raise ValueError("Node can't be validator and builder at same time!")

        logger.debug(
            "Initializing node",
            node_id=node_id,
            node_name=node_name,
            host=host,
            port=port,
            is_builder=is_builder,
            is_validator=is_validator,
            peer_count=len(peers)
        )

        self.dns = generate_keys(port)
        
        logger.info(
            "Node initialized successfully",
            node_id=node_id,
            node_name=node_name,
            dns=self.dns,
            endpoint=f"{host}:{port}"
        )

    def configuration(self, is_client: bool = True) -> QuicConfiguration:
        """
        Utility function to build quic configuration.
        Args:
            is_client (bool): Flag indicating node is a client
        Returns:
            config (QuicConfiguration): A QUIC Configuration
        """
        properties = {
            "is_client": is_client,
        }

        configuration = QuicConfiguration(**properties)
        configuration.load_cert_chain(f"seeds/{self.port}/cert.pem", f"seeds/{self.port}/key.pem")
        configuration.load_verify_locations(cafile=f"seeds/{self.port}/cert.pem")
        configuration.verify_mode = ssl.CERT_NONE

        configuration.max_data = 104857600  # 100 MB
        configuration.max_stream_data = 10485760  # 10 MB per stream
        configuration.max_datagram_size = 1350

        if is_client:
            configuration.server_name = self.dns

        if self.is_builder:
            configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}/builder"]
        else:
            configuration.alpn_protocols = [f"jamnp-s/{protocol_version}/{genesis_hash}", f"jamnp-s/{protocol_version}/{genesis_hash}/builder"]

        logger.debug(
            "QUIC configuration created",
            node_name=self.name,
            is_client=is_client,
            is_builder=self.is_builder,
            max_data_mb=configuration.max_data / (1024*1024),
            alpn_protocols=configuration.alpn_protocols
        )

        return configuration
    
    async def run_server(self):
        """
        Function to initialize server connection of the node.
        """
        session_ticket_store = SessionTicketStore(self.port)

        logger.info(
            "Starting QUIC server",
            node_name=self.name,
            host=self.host,
            port=self.port,
            endpoint=f"{self.host}:{self.port}"
        )

        server = await serve(
            self.host,
            self.port,
            configuration=self.configuration(is_client=False),
            create_protocol=QuicServerProtocol,
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
        )

        # Save server connection
        self.server = server
        
        logger.info(
            "QUIC server started successfully",
            node_name=self.name,
            endpoint=f"{self.host}:{self.port}"
        )

    async def connect_peer(self, peer: Peer):
        """
        Function to connect the node to a peer.
        """
        session_ticket_store = SessionTicketStore(self.port)

        try:
            # Skip self
            if peer.host == self.host and peer.port == self.port:
                logger.debug(
                    "Skipping self-connection",
                    node_name=self.name,
                    peer_endpoint=f"{peer.host}:{peer.port}",
                    self_endpoint=f"{self.host}:{self.port}"
                )
                return
            
            logger.info(
                "Establishing peer connection",
                node_name=self.name,
                peer_host=peer.host,
                peer_port=peer.port,
                peer_san=peer.san,
                peer_endpoint=f"{peer.host}:{peer.port}"
            )

            async with connect(
                    peer.host,
                    peer.port,
                    configuration=self.configuration(),
                    create_protocol=QuicClientProtocol,
                    session_ticket_handler=session_ticket_store.add,
            ) as client:

                # Save peer connection
                self.connections.append(client)
                client = cast(QuicClientProtocol, client)

                logger.info(
                    "Peer connection established",
                    node_name=self.name,
                    peer_endpoint=f"{peer.host}:{peer.port}",
                    connection_count=len(self.connections)
                )

                stream_id = client._quic.get_next_available_stream_id()
                
                # Send initial ping
                ping_message = json.dumps({
                    "type": "ping",
                    "from": self.name
                }).encode()
                
                client.stream_and_keep_open(stream_id=stream_id, message=ping_message)

                logger.debug(
                    "Initial ping sent to peer",
                    node_name=self.name,
                    peer_endpoint=f"{peer.host}:{peer.port}",
                    stream_id=stream_id,
                    message_size=len(ping_message)
                )

                # last_block = self.state.beta[-1]
                # final = Final(block_hash=last_block.header_hash, time_slot=U32(0))
                # await client.stream_and_keep_open(stream_id=stream_id, message=final.encode())

                self.peer_conn[peer] = stream_id, client
                self.is_initialized = True

                logger.info(
                    "Node initialization completed - peer connections active",
                    node_name=self.name,
                    total_connections=len(self.connections),
                    is_initialized=self.is_initialized
                )

                # Wait indefinitely - the connection will be managed by the context manager
                await asyncio.Future()

        except asyncio.CancelledError:
            logger.info(
                "Peer connection cancelled",
                node_name=self.name,
                peer_endpoint=f"{peer.host}:{peer.port}"
            )
        except Exception as e:
            logger.error(
                "Failed to establish peer connection",
                node_name=self.name,
                peer_endpoint=f"{peer.host}:{peer.port}",
                error=str(e),
                error_type=type(e).__name__
            )

    async def run_client(self):
        """
        Function to initialize client connections of the node.
        """
        logger.info(
            "Starting client connections",
            node_name=self.name,
            peer_count=len(self.peers)
        )
        
        tasks = []
        for peer in self.peers:
            task = asyncio.create_task(self.connect_peer(peer))
            tasks.append(task)
            
        logger.debug(
            "Created connection tasks for all peers",
            node_name=self.name,
            task_count=len(tasks)
        )
        
        await asyncio.gather(*tasks)

    async def initialize(self):
        """
        Function to fully initialize a node.
        """
        logger.info(
            "Starting node initialization",
            node_name=self.name,
            node_type="builder" if self.is_builder else "validator",
            endpoint=f"{self.host}:{self.port}"
        )

        if self.is_builder:
            logger.info(
                "Initializing builder node",
                node_name=self.name,
                endpoint=f"{self.host}:{self.port}"
            )

        if not self.is_builder:
            logger.info(
                "Starting validator server",
                node_name=self.name,
                endpoint=f"{self.host}:{self.port}"
            )
            await self.run_server()

            # Give server time to fully initialize
            await asyncio.sleep(1)
            
            logger.debug(
                "Server initialization complete, starting client connections",
                node_name=self.name
            )

        logger.info(
            "Opening connections to peers",
            node_name=self.name,
            peer_count=len(self.peers)
        )
        await self.run_client()
