from aioquic.asyncio import serve
# from aioquic.asyncio.server import QuicServer

from jam.network.playground.main import configuration
from jam.network.quic import QuicServerProtocol


async def run_server(host: str, port: int):
    server = await serve(
        host=host,
        port=port,
        configuration=configuration(port, is_client=False),
        create_protocol=QuicServerProtocol
    )

    print(f"Started Server {port}")

    return server