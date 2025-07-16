from tests.integration.utils.setup_processes import Client, Role, setup_processes
import os
import pytest
from jam.network.node import Node
from jam.logging import get_logger

CLIENTS = [
    Client(Role.VAL, 40000),
    Client(Role.PJAM, 2)
]

# Logger for WP Production
logger = get_logger("author")


async def node_tasks(node: Node):
    """Define Node tasks"""
    ...

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_block_sharing():
    await setup_processes(CLIENTS, None, 10)
