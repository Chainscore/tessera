import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from jam.accumulation.accumulation import Accumulation
from jam.assurances.assurances import Assurances
from jam.authorization.authorization import Authorization
from jam.disputes.disputes import Disputes
from jam.statistics.statistics import Statistics
from jam.types import Boolean
from jam.types.base.sequences.bytes import ByteArray32
from jam.preimages.preimages import Preimages
from jam.consensus.safrole.safrole import Safrole
from jam.recent_history.recent_history import RecentHistory
from jam.utils.shuffle import shuffle
from jam.state.utils.state_transformation import GeneralState
from jam.types.extrinsics.assurances import AssurancesExtrinsic
from jam.types.block import Block
from jam.types.extrinsics.disputes import DisputesExtrinsic
from jam.types.block import Extrinsic, Header
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic
from jam.types.extrinsics.preimages import PreimagesExtrinsic
from jam.types.extrinsics.tickets import TicketsExtrinsic
from jam.types.work.refine_context import RefineContext
from jam.types.work.item import WorkItem
from jam.types.work.package import WorkPackage
from jam.types.work.report import WorkReport
from jam.types.work.report import WorkResult

app = FastAPI()


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

class FileType(BaseModel):
    id : str

class RequestDataTypes(BaseModel):
    types : list[FileType]

# output or flags are optional entries
class RequestData(BaseModel):
    input: InputData
    output: OutputData | None = None
    flags: Any | None = None

class RequestDataShuffle(BaseModel):
    input: InputDataShuffle
    output: OutputDataShuffle

# Json to codec type formate
class InputDataCodec(BaseModel):
    file : Any
    label : Any

class RequestDataCodec(BaseModel):
    input : InputDataCodec

# codec to json types formate
class InputDataJson(BaseModel):
    file : Any
    label: Any

class RequestDataJson(BaseModel):
    input : InputDataJson

def fetch_type() :
    test_dir = Path(__file__).parent
    with open(test_dir / "type.json", "r") as f:
        type_json = json.load(f)

    return type_json

@app.get("/api/v1/types/validate", response_model=RequestDataTypes)
async def List_all_types():
    """ An overview of all available types. Only a subset of types is exposed here for testing. More will follow. """
    return fetch_type()

@app.post('/api/v1/types/type_id/json_to_codec/validate', status_code=200)
async def json_to_codec(request_data: RequestDataCodec):

    try:
        json_file = request_data.input.file
        label = request_data.input.label

        if label == "assurances_extrinsic":
            assurance = AssurancesExtrinsic.from_json(request_data.input.file)
            return {"data" : assurance.encode().hex(), "status" : "Ok"}

        elif label  == "block":
            block = Block.from_json(request_data.input.file)
            return {"data": block.encode().hex(), "status": "Ok"}

        elif label == "disputes_extrinsic":
            dispute = DisputesExtrinsic.from_json(request_data.input.file)
            return {"data": dispute.encode().hex(), "status": "Ok"}

        elif label  == "extrinsic":
            extrinsic = Extrinsic.from_json(request_data.input.file)
            return {"data": extrinsic.encode().hex(), "status": "Ok"}

        elif label == "guarantees_extrinsic":
            guarantee = GuaranteesExtrinsic.from_json(request_data.input.file)
            return {"data": guarantee.encode().hex(), "status": "Ok"}

        elif label == "header":
            header = Header.from_json(request_data.input.file)
            return {"data": header.encode().hex(), "status": "Ok"}

        elif label == "preimages_extrinsic":
            preimage = PreimagesExtrinsic.from_json(request_data.input.file)
            return {"data": preimage.encode().hex(), "status": "Ok"}

        elif label  == "refine_context":
            context = RefineContext.from_json(request_data.input.file)
            return {"data": context.encode().hex(), "status": "Ok"}

        elif label == "tickets_extrinsic":
            ticket = TicketsExtrinsic.from_json(request_data.input.file)
            return {"data": ticket.encode().hex(), "status": "Ok"}

        elif label  == "work_item":
            work_item = WorkItem.from_json(request_data.input.file)
            return {"data": work_item.encode().hex(), "status": "Ok"}

        elif label == "work_package":
            work_package = WorkPackage.from_json(request_data.input.file)
            return {"data": work_package.encode().hex(), "status": "Ok"}

        elif label  == "work_report":
            work_report = WorkReport.from_json(request_data.input.file)
            return {"data": work_report.encode().hex(), "status": "Ok"}

        elif label  == "work_result":
            work_result = WorkResult.from_json(request_data.input.file)
            return {"data": work_result.encode().hex(), "status": "Ok"}

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)

@app.post('/api/v1/types/type_id/codec_to_json/validate', status_code=200)
async def codec_to_json(request_data: RequestDataJson):

    try:
        label = request_data.input.label
        hex_string = request_data.input.file
        data = bytes.fromhex(hex_string)

        if label == "assurances_extrinsic":
            assurance, _ = AssurancesExtrinsic.decode_from(data)
            return {"data" : assurance.to_json(), "status" : "Ok"}

        elif label  == "block":
            block, _ = Block.decode_from(data)
            return {"data": block.to_json(), "status": "Ok"}

        elif label == "disputes_extrinsic":
            dispute, _ = DisputesExtrinsic.decode_from(data)
            return {"data": dispute.to_json(), "status": "Ok"}

        elif label  == "extrinsic":
            extrinsic, _ = Extrinsic.decode_from(data)
            return {"data": extrinsic.to_json(), "status": "Ok"}

        elif label == "guarantees_extrinsic":
            guarantee, _ = GuaranteesExtrinsic.decode_from(data)
            return {"data": guarantee.to_json(), "status": "Ok"}

        elif label == "header":
            header, _ = Header.decode_from(data)
            return {"data": header.to_json(), "status": "Ok"}

        elif label == "preimages_extrinsic":
            preimage, _ = PreimagesExtrinsic.decode_from(data)
            return {"data": preimage.to_json(), "status": "Ok"}

        elif label  == "refine_context":
            context, _ = RefineContext.decode_from(data)
            return {"data": context.to_json(), "status": "Ok"}

        elif label == "tickets_extrinsic":
            ticket, _ = TicketsExtrinsic.decode_from(data)
            return {"data": ticket.to_json(), "status": "Ok"}

        elif label  == "work_item":
            work_item, _ = WorkItem.decode_from(data)
            return {"data": work_item.to_json(), "status": "Ok"}

        elif label == "work_package":
            work_package, _ = WorkPackage.decode_from(data)
            return {"data": work_package.to_json(), "status": "Ok"}

        elif label  == "work_report":
            work_report, _ = WorkReport.decode_from(data)
            return {"data": work_report.to_json(), "status": "Ok"}

        elif label  == "work_result":
            work_result, _ = WorkResult.decode_from(data)
            return {"data": work_result.to_json(), "status": "Ok"}

    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(False)

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
        shuffle_sequence = shuffle(test_entropy, request_data.input.input)
        # if(shuffle_transition == request_data.output.output):
        return {"data": shuffle_sequence, "status": "Ok"}

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