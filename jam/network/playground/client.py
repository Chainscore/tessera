import asyncio

from jam.network.playground.main import connect_peer, Peer


async def run_client(port: int, host: str, peers: list[Peer]):
    """
    Function to initialize client connections of the node.
    """
    tasks = []
    for peer in peers:
        tasks.append(asyncio.create_task(connect_peer(host, port, peer)))
    await asyncio.gather(*tasks)