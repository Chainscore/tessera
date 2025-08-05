import ssl
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.logger import QuicLogger
from jam.network.base.certificate import generate_keys
from jam.network.base.sessions import SessionTicketStore
from jam.network.connection import NodeConnection
from jam.network.node import QuicNode
from jam.types.protocol.validators import ValidatorData
import socket 
import asyncio

from jam.utils.constants import NODE_ALPN

node: None|QuicNode = None

async def start_node(
    host: str,
    port: int,
    is_builder: bool = False,
) -> QuicNode:
    """
    Start a QUIC peer at the given `host` and `port`.
    """
    loop = asyncio.get_running_loop()

    from jam.state.state import state

    # await asyncio.sleep(10)
    
    # --- Socket --- #
    # Build one UDP socket, dual-stack, reusable
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:                                 # Linux only; ignore elsewhere
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except OSError:
        print("SO_REUSEPORT not supported on this platform, continuing without it")  # noqa: E501
        pass
    sock.bind((host, port))

    # --- Keys --- #
    san = generate_keys(port)
    
    # --- QUIC Configuration --- #
    cfg = QuicConfiguration(
        is_client=True,
        verify_mode=ssl.CERT_NONE, 
        max_data=(100*1024*1024), 
        max_stream_data=(10*1024*1024), 
        max_datagram_size=1350, 
        idle_timeout=120
    )
    cfg.quic_logger = QuicLogger()
    cfg.load_cert_chain(f"seeds/{port}/cert.pem", f"seeds/{port}/key.pem")
    cfg.alpn_protocols = [NODE_ALPN] 
    if is_builder:
        cfg.alpn_protocols[0] += ("/builder")

    # --- Session Ticket Store --- #
    session_ticket_store = SessionTicketStore(port)

    # --- Start Peer --- #
    _, proto = await loop.create_datagram_endpoint(
        lambda: QuicNode(
            id=san,
            cfg=cfg,
            create_protocol=lambda *args, **kwargs: NodeConnection(*args, **kwargs),
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
            retry=False,
            stream_handler=None,
        ),
        sock=sock
    )

    # if not is_builder:
    proto.set_neighbors()
    proto.port = port

    global node 
    node = proto

    # --- Connect with peers --- #
    from jam.settings import settings
    index = settings.validator_index
    peers = set(state.kappa)
    print("INDEX", index)
    if index != 7:
        peers.add(state.lambda_[index])
        peers.add(state.gamma.k[index])
        peers.add(state.iota[index])

    tasks = []
    for peer in peers:
        if peer.metadata.port == port:
            continue
        if port == 40006:
            print("BUILDER CONNECTING TO PEER", peer)
        # TODO: reconnect in 6 secs if still not connected
        tasks.append(asyncio.create_task(proto.connect(peer)))

    await asyncio.gather(*tasks)

    return proto
