from typing import Union
from fastapi import FastAPI
from markdown_it.rules_core import block
from pydantic import BaseModel
import json
from typing import Any, Dict, List

from requests import Request

from jam.statistics.statistics import Statistics
from yarl import Query

from jam.types import Boolean
from tests.unit.statistics.test_statistics_stf import create_block_from_input
from tests.unit.statistics.test_statistics_stf import create_state_from_pre
from tests.unit.statistics.test_statistics_stf import get_testcases_starting_with
from tests.unit.statistics.types import Testcase

app = FastAPI()

# async def get_json(request:  Request):
#     try:
#         raw_json = await request.json()
#         return raw
@app.get("/statistics")
async def read_item( block_data : str):
    # data = json.loads

    try:
        data = json.loads(block_data)
        vector = Testcase.from_json(data)
        test_block = create_block_from_input(vector.input)
        test_state = create_state_from_pre(vector.pre_state)
        output = Statistics.transition(test_state, test_block)
        assert output.pi[0] == vector.post_state.pi.current
        assert output.pi[1] == vector.post_state.pi.last

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)