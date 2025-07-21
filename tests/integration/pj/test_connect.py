from tests.integration.utils.setup_processes import Client, Role, setup_processes
import os
import pytest
from jam.logging import get_logger


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_1_peer():
    CLIENTS = [
        Client(Role.VAL, 40000 + int(os.environ.get("VAL", "0"))),
        Client(Role.PJAM, int(os.environ.get("PJAM", "4"))),
    ]
    await setup_processes(CLIENTS, None, 40)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_2_peer():
    CLIENTS = [
        Client(Role.VAL, 40000 + int(os.environ.get("VAL1", "0"))),
        Client(Role.VAL, 40000 + int(os.environ.get("VAL2", "1"))),
        Client(Role.PJAM, int(os.environ.get("PJAM", "4"))),
    ]
    await setup_processes(CLIENTS, None, 20)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_tiny_connections():
    CLIENTS = [
        Client(Role.VAL, 40000 + int(os.environ.get("VAL", "0"))),
        Client(Role.PJAM, int(os.environ.get("PJAM", "4"))),
    ]
    await setup_processes(CLIENTS, None, 20)

