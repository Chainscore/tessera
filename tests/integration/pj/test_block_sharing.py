from tests.integration.utils.setup_processes import Client, Role, setup_processes
import os
import pytest
from jam.logging import get_logger

CLIENTS = [
    Client(Role.VAL, 40001),
    Client(Role.PJAM, 4),
]

# Logger for WP Production
logger = get_logger("author")


async def node_tasks():
    """Define Node tasks"""
    ...
    # while True:
    #     
    #     for peer in node.peers:
            

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_block_sharing():
    await setup_processes(CLIENTS, None, 21)
