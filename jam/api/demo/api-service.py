import json
from pathlib import Path

from tsrkit_types import Bytes
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from jam.api.demo.models import ConversionSuccessResponse, ErrorResponse, RequestData, RequestDataCodec, RequestDataJson, RequestDataShuffle, RequestDataTypes, SuccessResponse
from typing import Dict, Union
from jam.accumulation.accumulation import Accumulation
from jam.assurances.assurances import Assurances
from jam.authorization.authorization import Authorization
from jam.disputes.disputes import Disputes
from jam.statistics.statistics import Statistics
from jam.preimages.preimages import Preimages
from jam.consensus.safrole.safrole import Safrole
from jam.consensus.safrole.errors import SafroleError
from jam.recent_history.recent_history import RecentHistory
from jam.utils.shuffle import shuffle
from jam.types.block import (
    Block, 
    Header, 
    DisputesExtrinsic,
    AssurancesExtrinsic,
    GuaranteesExtrinsic,
    PreimagesExtrinsic,
    TicketsExtrinsic,
)
from jam.types.block.extrinsics.extrinsic import Extrinsic
from jam.types.work import RefineContext
from jam.types.work import WorkItem
from jam.types.work import WorkPackage
from jam.types.work import WorkReport
from jam.types.work import WorkResult
from jam.state.ghost import GhostState

# Initialize FastAPI with metadata for Swagger UI
app = FastAPI(
    title="Tessera Node API",
    description="API for Tessera node state transitions, validations, and data conversions",
    version="1.0.0",
    openapi_tags=[
        {"name": "Types", "description": "Operations related to data types and type conversions"},
        {"name": "State Transitions", "description": "Validate state transitions for different components"},
        {"name": "Utilities", "description": "Utility operations for the blockchain"},
    ],
)


def fetch_type():
    """Fetch available types from type.json file"""
    test_dir = Path(__file__).parent
    with open(test_dir / "type.json", "r") as f:
        type_json = json.load(f)

    return type_json


@app.get("/api/v1/types/validate", 
         response_model=RequestDataTypes,
         tags=["Types"],
         summary="List all available types",
         description="Returns an overview of all available types in the system",
         responses={
             200: {"description": "List of available types"}
         })
async def list_all_types():
    """
    Get an overview of all available types.
    
    Only a subset of types is exposed here for testing. More will follow.
    """
    return fetch_type()

DATA_TYPES = {
    "assurances_extrinsic": AssurancesExtrinsic,
    "block": Block,
    "disputes_extrinsic": DisputesExtrinsic,
    "extrinsic": Extrinsic,
    "guarantees_extrinsic": GuaranteesExtrinsic,
    "header": Header,
    "preimages_extrinsic": PreimagesExtrinsic,
    "refine_context": RefineContext,
    "tickets_extrinsic": TicketsExtrinsic,
    "work_item": WorkItem,
    "work_package": WorkPackage,
    "work_report": WorkReport,
    "work_result": WorkResult
}

@app.post('/api/v1/types/type_id/json_to_codec/validate',
          status_code=status.HTTP_200_OK,
          tags=["Types"],
          summary="Convert JSON data to codec format",
          description="Converts JSON data to codec format based on specified type label",
          response_model=ConversionSuccessResponse,
          responses={
              200: {"description": "Successfully converted data"},
              400: {"description": "Invalid input data", "model": ErrorResponse},
              422: {"description": "Validation error"}
          })
async def json_to_codec(request_data: RequestDataCodec):
    """
    Convert JSON data to codec format.
    
    Takes JSON data and a type label, and returns the hex-encoded codec format.
    
    Available labels:
    - assurances_extrinsic: Assurances extrinsic data structure
    - block: Block data structure containing extrinsics and header  
    - disputes_extrinsic: Disputes extrinsic data structure
    - extrinsic: Generic extrinsic data structure
    - guarantees_extrinsic: Guarantees extrinsic data structure
    - header: Block header data structure
    - preimages_extrinsic: Preimages extrinsic data structure
    - refine_context: Refine context for work items
    - tickets_extrinsic: Tickets extrinsic data structure
    - work_item: Work item data structure
    - work_package: Work package data structure
    - work_report: Work report data structure
    - work_result: Work result data structure
    """
    try:
        label = request_data.input.label
        return {"data":  DATA_TYPES[label].from_json(request_data.input.file).encode().hex(), "status": "Ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


@app.post('/api/v1/types/type_id/codec_to_json/validate',
          status_code=status.HTTP_200_OK,
          tags=["Types"],
          summary="Convert codec data to JSON format",
          description="Converts hex-encoded codec data to JSON format based on specified type label",
          response_model=ConversionSuccessResponse,
          responses={
              200: {"description": "Successfully converted data"},
              400: {"description": "Invalid input data", "model": ErrorResponse},
              422: {"description": "Validation error"}
          })
async def codec_to_json(request_data: RequestDataJson):
    """
    Convert codec data to JSON format.
    
    Takes hex-encoded codec data and a type label, and returns the JSON representation.
    
    Available labels:
    - assurances_extrinsic: Assurances extrinsic data structure
    - block: Block data structure containing extrinsics and header  
    - disputes_extrinsic: Disputes extrinsic data structure
    - extrinsic: Generic extrinsic data structure
    - guarantees_extrinsic: Guarantees extrinsic data structure
    - header: Block header data structure
    - preimages_extrinsic: Preimages extrinsic data structure
    - refine_context: Refine context for work items
    - tickets_extrinsic: Tickets extrinsic data structure
    - work_item: Work item data structure
    - work_package: Work package data structure
    - work_report: Work report data structure
    - work_result: Work result data structure
    """
    try:
        label = request_data.input.label
        hex_string = request_data.input.file
        
        try:
            data = bytes.fromhex(hex_string)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid hex string")

        return {"data": DATA_TYPES[label].decode(data).to_json(), "status": "Ok"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


@app.post("/api/v1/safrole/validate",
          tags=["State Transitions"],
          summary="Validate Safrole state transition",
          description="Validates state transition according to Safrole consensus rules",
          responses={
              200: {"description": "Validation succeeded", "model": Dict[str, None]},
              400: {"description": "Validation failed", "model": ErrorResponse}
          })
async def safrole(request_data: RequestData):
    """
    Validate state transition according to Safrole consensus.
    
    Compares the output of the Safrole transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        entropy = getattr(request_data.input, 'entropy', None)
        if entropy is None:
            entropy = Bytes[32](32)

        transition_output = Safrole.transition(test_state, test_block, entropy)
        
        if request_data.output is None:
            return {"ok": None}
            
        output_state = GhostState.from_json(request_data.output.state).to_state()

        try:
            assert transition_output.tau == output_state.tau, "output_mismatch(tau)"
            assert transition_output.eta[0] == output_state.eta[0], "output_mismatch(eta)"
            assert transition_output.eta[1] == output_state.eta[1], "output_mismatch(eta)"
            assert transition_output.eta[2] == output_state.eta[2], "output_mismatch(eta)"
            assert transition_output.eta[3] == output_state.eta[3], "output_mismatch(eta)"
            assert transition_output.lambda_ == output_state.lambda_, "output_mismatch(lamda)"
            assert transition_output.kappa == output_state.kappa, "output_mismatch(kappa)"
            assert transition_output.gamma.k == output_state.gamma.k, "output_mismatch(gamma_k)"
            assert transition_output.iota == output_state.iota, "output_mismatch(iota)"
            assert transition_output.gamma.a == output_state.gamma.a, "output_mismatch(gamma_a)"
            assert transition_output.gamma.s == output_state.gamma.s, "output_mismatch(gamma_s)"
            assert transition_output.psi.offenders == output_state.psi.offenders, "output_mismatch(psi)"
            # TODO: uncomment this once KZG_commitment(⟦HB⟧) is implemented
            # assert len(transition_output.gamma.z) == len(output_state.gamma_z)
            # assert transition_output.gamma.z == output_state.gamma_z
        except AssertionError as e:
            return JSONResponse(status_code=400, content={"err": str(e)})

        return {"ok": None}

    except SafroleError as e:
        return JSONResponse(status_code=400, content={"err": e.code._value_})
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": "unexpected_error"})


@app.post("/api/v1/shuffle/validate",
          tags=["Utilities"],
          summary="Validate shuffling operation",
          description="Validates the shuffling of a sequence using the provided entropy",
          response_model=SuccessResponse,
          responses={
              200: {"description": "Shuffle result"},
              400: {"description": "Shuffle failed", "model": ErrorResponse}
          })
async def shuffle_validate(request_data: RequestDataShuffle):
    """
    Validate shuffling operation.
    
    Uses the provided entropy to shuffle the input sequence and returns the result.
    """
    try:
        test_entropy = request_data.input.entropy
        shuffle_sequence = shuffle(test_entropy, request_data.input.input)
        return {"data": shuffle_sequence, "status": "Ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Shuffle failed: {str(e)}")


@app.post("/api/v1/recent_history/validate",
          tags=["State Transitions"],
          summary="Validate Recent History state transition",
          description="Validates state transition according to Recent History rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def recent_history(request_data: RequestData):
    """
    Validate state transition according to Recent History rules.
    
    Compares the output of the Recent History transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        transition_output = RecentHistory.transition(test_state, test_block, ByteArray32([0]*32))
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GhostState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


@app.post("/api/v1/authorization/validate",
          tags=["State Transitions"],
          summary="Validate Authorization state transition",
          description="Validates state transition according to Authorization rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def authorization(request_data: RequestData):
    """
    Validate state transition according to Authorization rules.
    
    Compares the output of the Authorization transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        transition_output = Authorization.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GhostState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


@app.post("/api/v1/disputes/validate",
          tags=["State Transitions"],
          summary="Validate Disputes state transition",
          description="Validates state transition according to Disputes resolution rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def disputes(request_data: RequestData):
    """
    Validate state transition according to Disputes resolution rules.
    
    Compares the output of the Disputes transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        transition_output = Disputes.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GhostState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


@app.post("/api/v1/assurances/validate",
          tags=["State Transitions"],
          summary="Validate Assurances state transition",
          description="Validates state transition according to Assurances rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def assurances(request_data: RequestData):
    """
    Validate state transition according to Assurances rules.
    
    Compares the output of the Assurances transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        transition_output = Assurances.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GhostState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


@app.post("/api/v1/report/validate",
          tags=["State Transitions"],
          summary="Validate Report state transition",
          description="Validates state transition according to Report rules (incomplete)",
          responses={
              200: {"description": "Validation result"},
              400: {"description": "Validation failed", "model": ErrorResponse}
          })
async def report(request_data: RequestData):
    """
    Validate state transition according to Report rules.
    
    NOTE: This endpoint is incomplete and currently uses Assurances transition as a placeholder.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        ##TODO: Add reports once added.
        output = Assurances.transition(test_state, test_block)
        return {"result": output}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


@app.post("/api/v1/accumulate/validate",
          tags=["State Transitions"],
          summary="Validate Accumulation state transition",
          description="Validates state transition according to Accumulation rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def accumulate(request_data: RequestData):
    """
    Validate state transition according to Accumulation rules.
    
    Compares the output of the Accumulation transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        transition_output = Accumulation.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GhostState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


@app.post("/api/v1/preimages/validate",
          tags=["State Transitions"],
          summary="Validate Preimages state transition",
          description="Validates state transition according to Preimages rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def preimages(request_data: RequestData):
    """
    Validate state transition according to Preimages rules.
    
    Compares the output of the Preimages transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        transition_output = Preimages.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GhostState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})


@app.post("/api/v1/statistics/validate",
          tags=["State Transitions"],
          summary="Validate Statistics state transition",
          description="Validates state transition according to Statistics rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def statistics(request_data: RequestData):
    """
    Validate state transition according to Statistics rules.
    
    Compares the output of the Statistics transition function with the expected output state.
    """
    try:
        test_block = Block.from_json(request_data.input.block)
        test_state = GhostState.from_json(request_data.input.state).to_state()
        transition_output = Statistics.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
    
        output_state = GhostState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})
