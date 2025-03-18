from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import Any, Dict, List
from jam.accumulation.accumulation import Accumulation
from jam.assurances.assurances import Assurances
from jam.authorization.authorization import Authorization
from jam.disputes.disputes import Disputes
from jam.statistics.statistics import Statistics
from jam.types import Boolean
from jam.types.base.sequences.bytes import ByteArray32
from jam.preimages.preimages import Preimages
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

class InputData(BaseModel):
    block : Any
    state : Any

class InputDataShuffle(BaseModel):
    input : Any
    entropy: Any

class OutputDataShuffle(BaseModel):
    output : Any

class OutputData(BaseModel):
    state: Any


# output or flags are optional entries
class RequestData(BaseModel):
    input: InputData
    output: OutputData | None = None
    flags: Any | None = None

class RequestDataShuffle(BaseModel):
    input: InputDataShuffle
    output: OutputDataShuffle

@app.post("/api/v1/safrole/validate")
async def safrole(request_data: RequestData):
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()

        transition_output = Safrole.transition(test_state, test_block)
        print("conversion successs")
        output_state = GeneralState.from_json(request_data.output.state).to_state()
        if (transition_output == output_state):
            return Boolean(True)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)

    return Boolean(False)


@app.post("/api/v1/shuffle/validate")
async def shuffle_validate(request_data: RequestDataShuffle):

    try:
        test_entropy = request_data.input.entropy
        shuffle_transition = shuffle(test_entropy, request_data.input.input)
        if(shuffle_transition == request_data.output.output):
            return Boolean(True);

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)

    return Boolean(False)

@app.post("/api/v1/recent_history/validate")
async def recent_history(request_data: RequestData):
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = RecentHistory.transition(test_state, test_block, ByteArray32([0]*32))
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return Boolean(True)
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)

@app.post("/api/v1/authorization/validate")
async def authorization(request_data: RequestData):
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Authorization.transition(test_state, test_block)
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return Boolean(True)
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)


@app.post("/api/v1/disputes/validate")
async def disputes(request_data: RequestData):
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Disputes.transition(test_state, test_block)
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return Boolean(True)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)

@app.post("/api/v1/assurances/validate")
async def assurances(request_data: RequestData):

    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Assurances.transition(test_state, test_block)
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            print("conversion success")
            return Boolean(True)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)

@app.post("/api/v1/report/validate")
async def report(request_data: RequestData):
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        ##TODO: Add reports once added.
        output = Assurances.transition(test_state, test_block)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return output

@app.post("/api/v1/accumulate/validate")
async def accumulate(request_data: RequestData):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Accumulation.transition(test_state, test_block)
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return Boolean(True)

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)

@app.post("/api/v1/preimages/validate")
async def preimages(request_data: RequestData):
    # data = json.loads
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Preimages.transition(test_state, test_block)
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return Boolean(True)
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)

@app.post("/api/v1/statistics/validate")
async def statistics(request_data: RequestData):
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Statistics.transition(test_state, test_block)
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return Boolean(True)
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)
