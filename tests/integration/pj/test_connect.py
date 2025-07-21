import asyncio
from time import time
from jam.utils.constants import GENESIS_TS
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
        Client(Role.VAL, 40000 + int(os.environ.get("VAL2", "1"))),
        Client(Role.VAL, 40000 + int(os.environ.get("VAL2", "1"))),
        Client(Role.VAL, 40000 + int(os.environ.get("VAL2", "1"))),
        Client(Role.PJAM, int(os.environ.get("PJAM", "4"))),
    ]

    async def node_task():
        from jam.network.start import node 
        from jam.logging import get_logger
        logger = get_logger()
        ts = int((time() - GENESIS_TS) // 6)
        while True:
            if node:
                logger.info(
                    "Node operations started for a new timeslot", 
                    time_slot=ts, 
                    peers=len(node.active_peers), 
                    connections=len(node.all_connected)
                )
                ts+=1 
            await asyncio.sleep(6)
    await setup_processes(CLIENTS, node_task, 40)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_tiny_connections():
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.PJAM, 1),
        Client(Role.VAL, 40000 + 2),
        Client(Role.VAL, 40000 + 3),
        Client(Role.VAL, 40000 + 4),
        Client(Role.VAL, 40000 + 5),
    ]
    async def node_task():
        from jam.network.start import node 
        from jam.logging import get_logger
        logger = get_logger()
        ts = int((time() - GENESIS_TS) // 6)
        while True:
            if node:
                logger.info(
                    "Node operations started for a new timeslot", 
                    time_slot=ts, 
                    peers=len(node.active_peers), 
                    connections=len(node.all_connected)
                )
                ts+=1 
            await asyncio.sleep(6)   
    await setup_processes(CLIENTS, node_task, 40)

