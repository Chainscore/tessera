from multiprocessing import Process
import pytest
import os

from tests.integration.utils.setup_processes import Client, Role, setup_processes

CLIENTS = [Client(Role.PJAM, 1)]


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_start_pj():
    await setup_processes(CLIENTS, None, 4)
