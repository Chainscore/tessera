from typing import Union, Optional
from fastapi import FastAPI
# from markdown_it.rules_core import block
from pydantic import BaseModel
import json
from typing import Any, Dict, List
from requests import Request
from jam.consensus.safrole.safrole import  Safrole
from jam.state.state import State
from jam.statistics.statistics import Statistics
from yarl import Query
from jam.types import Boolean
from tests.unit.statistics.test_statistics_stf import create_block_from_input
from tests.unit.statistics.test_statistics_stf import create_state_from_pre
from tests.unit.statistics.test_statistics_stf import get_testcases_starting_with
from tests.unit.statistics.types import Testcase, PreState
from jam.types.block import Block
from jam.consensus.safrole.safrole import Safrole
from jam.recent_history.recent_history import RecentHistory
from jam.utils.shuffle import shuffle

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
async def vaildate_safarole(request_data: RequestDataSafarole):
    # data = json.loads
    try:

        test_block = Block.from_json(request_data.input.block)
        # test_state = PreState.from_json(request_data.input.state)
        # state_from_prestate = create_state_from_pre(test_state)
        output = Safrole.transition(request_data.input.state, test_block)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)

@app.post("/api/v1/shuffle/validate")
async def vaildate_shuffle(request_data: RequestDataShuffle):
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

