import asyncio
from time import time
from jam.operations import operate
from jam.utils.constants import GENESIS_TS
from tests.integration.utils.setup_processes import Client, Role, setup_processes, setup_processes_with_delay
import os
import pytest


async def node_info_printer():
    from jam.log_setup import node_logger as logger

    ts = int((time() - GENESIS_TS) // 6)
    while True:
        from jam.network.start import node 
        if node:
            logger.info(
                "Node operations started for a new timeslot", 
                time_slot=ts, 
                peers=len(node.active_peers), 
                connections=len(node.all_connected)
            )
        ts += 1
        await asyncio.sleep(6)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_1_tsr_1_pjam():
    CLIENTS = [
        Client(Role.VAL, 40000 + int(os.environ.get("VAL", "1"))),
        Client(Role.PJAM, int(os.environ.get("PJAM", "0"))),
    ]
    await setup_processes(CLIENTS, [operate], 240)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_2_tsr():
    CLIENTS = [
        Client(Role.VAL, 40000 + int(os.environ.get("VAL1", "0"))),
        Client(Role.VAL, 40000 + int(os.environ.get("VAL2", "1"))),
    ]

    await setup_processes(CLIENTS, [operate], 80)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_2_tsr_1_pjam():
    # In this config: 3 -> 1, 1 -> 0; 1 should have 2 peers
    CLIENTS = [
        Client(Role.VAL, 40000 + int(os.environ.get("VAL1", "0"))),
        Client(Role.VAL, 40000 + int(os.environ.get("VAL2", "3"))),
        Client(Role.PJAM, int(os.environ.get("PJAM", "1"))),
    ]

    await setup_processes(CLIENTS, [operate], 80)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_1_tsr_2_pjam():
    # In this config: 3 -> 1, 1 -> 0; 1 should have 2 peers
    CLIENTS = [
        Client(Role.VAL, 40000 + int(os.environ.get("VAL", "0"))),
        Client(Role.PJAM, int(os.environ.get("PJAM1", "1"))),
        Client(Role.PJAM, int(os.environ.get("PJAM2", "2"))),
    ]

    await setup_processes(CLIENTS, [node_info_printer], 80)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_tiny_tsr(rpc):
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.VAL, 40000 + 1),
        Client(Role.VAL, 40000 + 2),
        Client(Role.VAL, 40000 + 3),
        Client(Role.VAL, 40000 + 4),
        Client(Role.VAL, 40000 + 5),
    ]
    
    await setup_processes(CLIENTS, [operate], 2400, rpc_flag=rpc)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_tiny_tsr_1_pjam():
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.PJAM, 1),
        Client(Role.VAL, 40000 + 2),
        Client(Role.VAL, 40000 + 3),
        Client(Role.VAL, 40000 + 4),
        Client(Role.VAL, 40000 + 5),
    ]
    
    await setup_processes(CLIENTS, [operate], 240)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_tiny_tsr_5_pjam():
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.PJAM, 1),
        Client(Role.PJAM, 2),
        Client(Role.PJAM, 3),
        Client(Role.PJAM, 4),
        Client(Role.PJAM, 5),
    ]
    
    await setup_processes(CLIENTS, [operate], 2400)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_tiny_2_tsr_4_pjam():
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.VAL, 40000 + 1),
        Client(Role.PJAM, 2),
        Client(Role.PJAM, 3),
        Client(Role.PJAM, 4),
        Client(Role.PJAM, 5),
    ]

    await setup_processes(CLIENTS, [operate], 2400)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_tiny_3_tsr_3_pjam():
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.VAL, 40000 + 1),
        Client(Role.VAL, 40000 + 2),
        Client(Role.PJAM, 3),
        Client(Role.PJAM, 4),
        Client(Role.PJAM, 5),
    ]

    await setup_processes(CLIENTS, [operate], 2400)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_5_pjam():
    CLIENTS = [
        Client(Role.PJAM, 1),
        Client(Role.PJAM, 2),
        Client(Role.PJAM, 3),
        Client(Role.PJAM, 4),
        Client(Role.PJAM, 5),
    ]

    await setup_processes(CLIENTS, [operate], 2400)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_1_pjam():
    CLIENTS = [
        Client(Role.PJAM, 0),
    ]

    await setup_processes(CLIENTS, [operate], 2400)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_5_tsr():
    CLIENTS = [
        Client(Role.VAL, 40000 + 1),
        Client(Role.VAL, 40000 + 2),
        Client(Role.VAL, 40000 + 3),
        Client(Role.VAL, 40000 + 4),
        Client(Role.VAL, 40000 + 5),
    ]

    await setup_processes(CLIENTS, [operate], 2400)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_sync(rpc):
    CLIENTS = [
        Client(Role.VAL, 40000 + 0),
        Client(Role.VAL, 40000 + 5),
        Client(Role.VAL, 40000 + 3),
        Client(Role.VAL, 40000 + 1),
        Client(Role.VAL, 40000 + 4),
        Client(Role.VAL, 40000 + 2),
    ]

    await setup_processes_with_delay(CLIENTS, [operate], 2400, rpc_flag=rpc, delay=50)
