from typing import Union, Optional
from fastapi import FastAPI
# from markdown_it.rules_core import block
from pydantic import BaseModel
import json
from typing import Any, Dict, List
from requests import Request

from jam.accumulation.accumulation import Accumulation
from jam.assurances.assurances import Assurances
from jam.authorization.authorization import Authorization
from jam.consensus.safrole.safrole import  Safrole
from jam.disputes.disputes import Disputes
from jam.state.state import State
from jam.statistics.statistics import Statistics
from yarl import Query
from jam.types import Boolean
from jam.types.base.sequences.bytes import ByteArray32
from jam.preimages.preimages import Preimages

from tests.unit.statistics.test_statistics_stf import create_block_from_input
from tests.unit.statistics.test_statistics_stf import create_state_from_pre
from tests.unit.statistics.test_statistics_stf import get_testcases_starting_with
from tests.unit.statistics.types import Testcase, PreState
from jam.types.block import Block
from jam.consensus.safrole.safrole import Safrole
from jam.recent_history.recent_history import RecentHistory
from jam.utils.shuffle import shuffle
from jam.state.utils.state_transformation import GeneralState


app = FastAPI()

# json format
# json={
#         "input": {"block": input_data, "state": pre_state},
#         "output": {"state": post_state},
#         "flags": {"size": "tiny", "active": True}
#     }
class InputDataSafarole(BaseModel):
    block : Any
    state : Any

class InputDataShuffle(BaseModel):
    input : Any
    entropy: Any


class RequestDataSafarole(BaseModel):
    input: InputDataSafarole


class RequestDataShuffle(BaseModel):
    input: InputDataShuffle
    print("Runs")

@app.post("/api/v1/safrole/validate")
async def safarole(request_data: RequestDataSafarole):
    # data = json.loads
    try:

        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Safrole.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/shuffle/validate")
async def shuffle(request_data: RequestDataShuffle):
    # data = json.loads
    try:
        print(request_data.input.entropy)
        test_entropy = request_data.input.entropy.e
        output = shuffle(request_data.input.input, request_data.input.entropy)
        print("rinfs")
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/recent_history/validate")
async def recent_history(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = RecentHistory.transition(test_state, test_block, ByteArray32([0]*32))
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/authorization/validate")
async def authorization(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Authorization.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)


@app.post("/api/v1/disputes/validate")
async def disputes(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Disputes.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)


@app.post("/api/v1/disputes/validate")
async def disputes(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Disputes.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/assurances/validate")
async def assurances(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Assurances.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/report/validate")
async def report(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        ##TODO: Add reports once added.
        output = Assurances.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/accumulate/validate")
async def accumulate(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Accumulation.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/preimages/validate")
async def preimages(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Preimages.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/statistics/validate")
async def statistics(request_data: RequestDataSafarole):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        output = Statistics.transition(test_state, test_block)
        print(output)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)
