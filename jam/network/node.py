import ssl
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.logger import QuicLogger
from jam.network.base.jamnp import JAMNP
from jam.network.base.sessions import SessionTicketStore
from jam.types.protocol.validators import ValidatorData
from .peer import QuicPeer
import socket 
import asyncio

node: None|QuicPeer = None


genesis_hash = "b5af8eda"
protocol_version = "0"
node_alpn = f"jamnp-s/{protocol_version}/{genesis_hash}"
builder_alpn = node_alpn + "/builder"


async def start_node(
    host: str,
    port: int,
    peer_infos: list[ValidatorData],
    is_light_node: bool = False,
) -> QuicPeer:
    """
    Start a QUIC peer at the given `host` and `port`.
    """

    loop = asyncio.get_running_loop()
    
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
    
    # --- QUIC Configuration --- #
    common_args = {
        "verify_mode": ssl.CERT_NONE, 
        "max_data": (100*1024*1024), 
        "max_stream_data": (10*1024*1024), 
        "max_datagram_size": 1550, 
        "idle_timeout": 120
    }

    client_cfg = QuicConfiguration(is_client=True, **common_args)
    server_cfg = QuicConfiguration(is_client=is_light_node, **common_args)
    server_cfg.quic_logger = QuicLogger()

    server_cfg.load_cert_chain(f"seeds/{port}/cert.pem", f"seeds/{port}/key.pem")
    server_cfg.alpn_protocols = [node_alpn, builder_alpn]

    client_cfg.load_cert_chain(f"seeds/{port}/cert.pem", f"seeds/{port}/key.pem")
    client_cfg.alpn_protocols = [node_alpn, builder_alpn]


    # --- Session Ticket Store --- #
    session_ticket_store = SessionTicketStore(port)

    # --- Start Peer --- #
    _, proto = await loop.create_datagram_endpoint(
        lambda: QuicPeer(
            server_cfg=server_cfg,
            client_cfg=client_cfg,
            create_protocol=lambda *args, **kwargs: JAMNP(*args, **kwargs),
            session_ticket_fetcher=session_ticket_store.pop,
            session_ticket_handler=session_ticket_store.add,
            retry=False,
            stream_handler=None,
        ),
        sock=sock
    )

    await asyncio.sleep(2)

    # --- Connect with peers --- #
    tasks = []
    for peer in peer_infos:
        if peer.metadata.port == port:
            continue
        # TODO: reconnect in 6 secs if still not connected
        tasks.append(asyncio.create_task(proto.connect(peer)))
    
    await asyncio.gather(*tasks)

    global node 
    node = proto
    return proto
