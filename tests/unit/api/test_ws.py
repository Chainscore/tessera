import os
import pytest
import asyncio
import json

from tsrkit_types import U32, Bytes

from jam.block.block import Block
from jam.api.rpc.app import rpc as quart
from jam.types.protocol.core import TimeSlot, ServiceId
from jam.types.protocol.crypto import Hash

from tests.unit.api.utils import produce_chain, init_chain, tweak_service, tweak_storage, tweak_lookup


# Refred this : https://quart.palletsprojects.com/en/latest/how_to_guides/websockets/

def request(method: str, params: list = []):
    return {
        "jsonrpc": "2.0",
        "id": 101,
        "method": method,
        "params": params
    }


target_code = bytes([0, 0, 22, 124, 121, 81, 25, 1, 7, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50, 0, 69, 147, 18])
target_code_hash = Hash.blake2b(target_code)
target_service = ServiceId(69)
target_key = Bytes(b"created")
target_val = Bytes(b"custom service created for test by batman")

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_ws_finalized_block(db_path, rpc):
    if not rpc:
        raise ConnectionError("RPC Connections Closed")

    method = "subscribeFinalizedBlock"

    # ——— set up on‐chain state just like the Node ———
    state, settings, b0 = init_chain(db_path, rpc)

    async with quart.test_client() as client:
        async with client.websocket("/") as ws:
            await ws.send(json.dumps(request(method)))
            await asyncio.sleep(0.1)

            #  Subscription Acknowledgement
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data["id"] == 101
            assert data["result"] is not None

            state, settings = produce_chain(db_path, False, rpc)
            i = 1
            while True:
                raw = await asyncio.wait_for(ws.receive(), timeout=5)
                data = json.loads(raw)

                block = Block.load_w_ts(TimeSlot(i), settings.main_db)
                expected = [list(block.header.hash()), int(block.header.slot)]
                assert data["method"] == method
                assert data["params"]["result"] is not None
                assert data["params"]["result"]["header_hash"] == expected[0]
                assert data["params"]["result"]["slot"] == expected[1]

                i += 1
                if i == 6:
                    return


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_ws_best_block(db_path, rpc):
    if not rpc:
        raise ConnectionError("RPC Connections Closed")

    method = "subscribeBestBlock"

    # ——— mirror the HTTP setup for bestBlock ———
    # state, settings, b0 = init_chain(db_path, rpc)

    #  open a WS & subscribe to the function
    async with quart.test_client() as client:
        async with client.websocket("/") as ws:
            await ws.send(json.dumps(request(method)))
            await asyncio.sleep(0.01)

            #  Subscription Acknowledgement
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data["id"] == 101
            assert data["result"] is not None

            state, settings = produce_chain(db_path, True, rpc)

            i = 0
            while True:
                raw = await asyncio.wait_for(ws.receive(), timeout=5)
                data = json.loads(raw)

                block = Block.load_w_ts(TimeSlot(i), settings.main_db)
                expected = [list(block.header.hash()), int(block.header.slot)]

                # Assertions
                assert data["method"] == method
                assert data["params"]["result"] is not None
                assert data["params"]["result"]["header_hash"] == expected[0]
                assert data["params"]["result"]["slot"] == expected[1]

                i += 1
                if i == 6:
                    return


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_ws_statistics(db_path, rpc):
    if not rpc:
        raise ConnectionError("RPC Connections Closed")

    method = "subscribeStatistics"
    params = [ False ]

    state, settings, b0 = init_chain(db_path, rpc)

    # open WS, subscribe, then read until ith slot’s update arrives
    async with quart.test_client() as client:
        async with client.websocket("/") as ws:
            await ws.send(json.dumps(request(method, params)))
            await asyncio.sleep(1)

            #  Subscription Acknowledgement
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data["id"] == 101
            assert data["result"] is not None

            target_slot = TimeSlot(1)

            # Simulate Chain
            b1 = b0.produce(target_slot, state)
            state.transition(b1)

            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            block_hash = b1.header.hash()

            # compute the expected Pi vector at slot i
            expected_pi = list(state.pi.encode())

            # Assertions
            assert data["method"] == method
            assert data["params"]["result"] is not None
            assert data["params"]["result"]["slot"] == target_slot
            assert data["params"]["result"]["header_hash"] == list(block_hash)
            assert data["params"]["result"]["value"] == expected_pi


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_ws_service_data(db_path, rpc):
    if not rpc:
        raise ConnectionError("RPC Connections Closed")

    method = "subscribeServiceData"
    params = [ target_service, True ]

    state, settings, b0 = init_chain(db_path, rpc)

    async with quart.test_client() as client:
        async with client.websocket("/") as ws:
            await ws.send(json.dumps(request(method, params)))
            await asyncio.sleep(1)

            #  Subscription Acknowledgement
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data["id"] == 101
            assert data["result"] is not None

            # Simulate Chain
            b1 = b0.produce(TimeSlot(1), state)
            state.transition(b1)

            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            # Assertions
            # Handle Case when service is not set
            assert data["method"] == method
            assert data["params"]["result"] is not None
            assert data["params"]["result"]["value"] is None

            service_data = tweak_service(target_service, target_code_hash, target_code)
            i = 0

            # Catch All Service Data Changes, when any account field or account data changes
            while True:
                raw = await asyncio.wait_for(ws.receive(), timeout=5)
                data = json.loads(raw)

                expected_data = service_data
                expected_data.num_i += 2 * i

                # Assertions
                assert data["method"] == method
                assert data["params"]["result"] is not None
                assert data["params"]["result"]["value"] == list(expected_data.encode())

                i += 1
                if i == 2:
                    return



@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_ws_service_value(db_path, rpc):
    if not rpc:
        raise ConnectionError("RPC Connections Closed")

    method = "subscribeServiceValue"
    params = [target_service, list(target_key), False]

    state, settings, b0 = init_chain(db_path, rpc)

    async with quart.test_client() as client:
        async with client.websocket("/") as ws:
            await ws.send(json.dumps(request(method, params)))
            await asyncio.sleep(1)

            #  Subscription Acknowledgement
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data["id"] == 101
            assert data["result"] is not None

            # Simulate Chain
            b1 = b0.produce(TimeSlot(1), state)
            state.transition(b1)

            # Catch Initial Call for subscription
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            # Assertions
            # Handle Case when service is not set
            assert data["method"] == method
            assert data["params"]["result"] is not None
            assert data["params"]["result"]["value"] is None

            tweak_storage(target_service, target_code_hash, target_key, target_val)

            # Catch Service Value changes
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            # Assertions
            assert data["method"] == method
            assert data["params"]["result"] is not None
            assert data["params"]["result"]["value"] == list(target_val)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_ws_service_preimage(db_path, rpc):
    if not rpc:
        raise ConnectionError("RPC Connections Closed")

    method = "subscribeServicePreimage"
    params = [target_service, list(target_code_hash), False]

    state, settings, b0 = init_chain(db_path, rpc)

    async with quart.test_client() as client:
        async with client.websocket("/") as ws:
            await ws.send(json.dumps(request(method, params)))
            await asyncio.sleep(1)

            #  Subscription Acknowledgement
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data["id"] == 101
            assert data["result"] is not None

            # Simulate Chain
            b1 = b0.produce(TimeSlot(1), state)
            state.transition(b1)

            # Catch Initial Call for subscription
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            # Assertions
            # Handle Case when service is not set
            assert data["method"] == method
            assert data["params"]["result"] is not None
            assert data["params"]["result"]["value"] is None

            tweak_service(target_service, target_code_hash, target_code)

            # Catch Service Value changes
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            # Assertions
            assert data["method"] == method
            assert data["params"]["result"] is not None
            assert data["params"]["result"]["value"] == list(target_code)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_ws_service_request(db_path, rpc):
    if not rpc:
        raise ConnectionError("RPC Connections Closed")

    method = "subscribeServiceRequest"
    params = [target_service, list(target_code_hash), len(target_code), False]

    state, settings = produce_chain(db_path, True, rpc)

    async with quart.test_client() as client:
        async with client.websocket("/") as ws:
            await ws.send(json.dumps(request(method, params)))
            await asyncio.sleep(1)

            #  Subscription Acknowledgement
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data["id"] == 101
            assert data["result"] is not None

            # Catch Initial Call for subscription
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            # Assertions
            # Handle Case when service is not set
            assert data["method"] == method
            assert data["params"]["result"] is not None
            assert data["params"]["result"]["value"] is None

            tweak_lookup(target_service, target_code_hash, target_code)

            expected_lookup = []

            # Catch Service Value changes
            i = 0
            while i < 4:
                if i > 0:
                    expected_lookup.append(2*i - 1)

                raw = await asyncio.wait_for(ws.receive(), timeout=5)
                data = json.loads(raw)

                # Assertions
                assert data["method"] == method
                assert data["params"]["result"] is not None
                assert data["params"]["result"]["value"] == expected_lookup

                i +=1