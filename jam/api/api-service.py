import json
from enum import Enum
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union, Literal
from jam.accumulation.accumulation import Accumulation
from jam.assurances.assurances import Assurances
from jam.authorization.authorization import Authorization
from jam.disputes.disputes import Disputes
from jam.statistics.statistics import Statistics
from jam.types import Boolean
from jam.types.base.sequences.bytes import ByteArray32
from jam.preimages.preimages import Preimages
from jam.consensus.safrole.safrole import Safrole
from jam.consensus.safrole.errors import SafroleError
from jam.recent_history.recent_history import RecentHistory
from jam.utils.shuffle import shuffle
from jam.state.utils.state_transformation import GeneralState
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

# Response Models
class SuccessResponse(BaseModel):
    status: str = Field("Ok", description="Status of the operation")
    data: Any = Field(None, description="The operation result data")

class ErrorResponse(BaseModel):
    err: str = Field(..., description="Error message or code")

class ConversionSuccessResponse(BaseModel):
    data: str = Field(..., description="Converted data in hex format or JSON structure")
    status: str = Field("Ok", description="Status of the operation")

# Input/Output Models
class InputData(BaseModel):
    block: Dict[str, Any] = Field(..., description="Block data in JSON format")
    state: Dict[str, Any] = Field(..., description="State data in JSON format")
    entropy: Optional[Any] = Field(None, description="Optional entropy for randomization")

class InputDataShuffle(BaseModel):
    input: List[Any] = Field(..., description="Input sequence to shuffle")
    entropy: Any = Field(..., description="Entropy for shuffling")

class OutputDataShuffle(BaseModel):
    output: List[Any] = Field(..., description="Expected shuffled output")

class OutputData(BaseModel):
    state: Dict[str, Any] = Field(..., description="Expected output state in JSON format")

class FileType(BaseModel):
    id: str = Field(..., description="Type identifier")

class RequestDataTypes(BaseModel):
    types: list[FileType] = Field(..., description="List of available type identifiers")

# Request models with proper field descriptions
class RequestData(BaseModel):
    input: InputData = Field(..., description="Input data for validation")
    output: Optional[OutputData] = Field(None, description="Expected output for validation")
    flags: Optional[Dict[str, Any]] = Field(None, description="Optional flags for validation")

class RequestDataShuffle(BaseModel):
    input: InputDataShuffle = Field(..., description="Input data for shuffle validation")
    output: OutputDataShuffle = Field(..., description="Expected output after shuffling")

# Define the literal types for codec labels
CodecLabelType = Literal[
    "assurances_extrinsic", 
    "block", 
    "disputes_extrinsic", 
    "extrinsic", 
    "guarantees_extrinsic", 
    "header", 
    "preimages_extrinsic", 
    "refine_context", 
    "tickets_extrinsic", 
    "work_item", 
    "work_package", 
    "work_report", 
    "work_result"
]

# Labels with descriptions
LABEL_DESCRIPTIONS = {
    "assurances_extrinsic": "Assurances extrinsic data structure",
    "block": "Block data structure containing extrinsics and header",
    "disputes_extrinsic": "Disputes extrinsic data structure",
    "extrinsic": "Generic extrinsic data structure",
    "guarantees_extrinsic": "Guarantees extrinsic data structure",
    "header": "Block header data structure",
    "preimages_extrinsic": "Preimages extrinsic data structure",
    "refine_context": "Refine context for work items",
    "tickets_extrinsic": "Tickets extrinsic data structure",
    "work_item": "Work item data structure",
    "work_package": "Work package data structure",
    "work_report": "Work report data structure",
    "work_result": "Work result data structure"
}

# Type labels as enum for documentation
class TypeLabelEnum(str, Enum):
    """Available type labels for conversion between JSON and codec formats"""
    ASSURANCES_EXTRINSIC = "assurances_extrinsic"
    BLOCK = "block"
    DISPUTES_EXTRINSIC = "disputes_extrinsic"
    EXTRINSIC = "extrinsic"
    GUARANTEES_EXTRINSIC = "guarantees_extrinsic"
    HEADER = "header"
    PREIMAGES_EXTRINSIC = "preimages_extrinsic"
    REFINE_CONTEXT = "refine_context"
    TICKETS_EXTRINSIC = "tickets_extrinsic"
    WORK_ITEM = "work_item"
    WORK_PACKAGE = "work_package"
    WORK_REPORT = "work_report"
    WORK_RESULT = "work_result"

# Json to codec type format
class InputDataCodec(BaseModel):
    file: Dict[str, Any] = Field(
        ..., 
        description="JSON file content to convert to codec format"
    )
    label: str = Field(
        ..., 
        description="Type label for conversion",
        enum=[
            "assurances_extrinsic", 
            "block", 
            "disputes_extrinsic", 
            "extrinsic", 
            "guarantees_extrinsic", 
            "header", 
            "preimages_extrinsic", 
            "refine_context", 
            "tickets_extrinsic", 
            "work_item", 
            "work_package", 
            "work_report", 
            "work_result"
        ]
    )

    class Config:
        schema_extra = {
            "example": {
                "file": {},
                "label": "block"
            }
        }

class RequestDataCodec(BaseModel):
    input: InputDataCodec = Field(..., description="Input data for JSON to codec conversion")

# Codec to JSON format
class InputDataJson(BaseModel):
    file: str = Field(
        ..., 
        description="Hex-encoded codec data to convert to JSON",
        example="0a1b2c3d4e5f"
    )
    label: str = Field(
        ..., 
        description="Type label for conversion",
        enum=[
            "assurances_extrinsic", 
            "block", 
            "disputes_extrinsic", 
            "extrinsic", 
            "guarantees_extrinsic", 
            "header", 
            "preimages_extrinsic", 
            "refine_context", 
            "tickets_extrinsic", 
            "work_item", 
            "work_package", 
            "work_report", 
            "work_result"
        ]
    )

    class Config:
        schema_extra = {
            "example": {
                "file": "0a1b2c3d4e5f",
                "label": "block"
            }
        }

class RequestDataJson(BaseModel):
    input: InputDataJson = Field(..., description="Input data for codec to JSON conversion")


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
        json_file = request_data.input.file
        label = request_data.input.label

        if label == "assurances_extrinsic":
            assurance = AssurancesExtrinsic.from_json(request_data.input.file)
            return {"data": assurance.encode().hex(), "status": "Ok"}

        elif label == "block":
            block = Block.from_json(request_data.input.file)
            return {"data": block.encode().hex(), "status": "Ok"}

        elif label == "disputes_extrinsic":
            dispute = DisputesExtrinsic.from_json(request_data.input.file)
            return {"data": dispute.encode().hex(), "status": "Ok"}

        elif label == "extrinsic":
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

        elif label == "refine_context":
            context = RefineContext.from_json(request_data.input.file)
            return {"data": context.encode().hex(), "status": "Ok"}

        elif label == "tickets_extrinsic":
            ticket = TicketsExtrinsic.from_json(request_data.input.file)
            return {"data": ticket.encode().hex(), "status": "Ok"}

        elif label == "work_item":
            work_item = WorkItem.from_json(request_data.input.file)
            return {"data": work_item.encode().hex(), "status": "Ok"}

        elif label == "work_package":
            work_package = WorkPackage.from_json(request_data.input.file)
            return {"data": work_package.encode().hex(), "status": "Ok"}

        elif label == "work_report":
            work_report = WorkReport.from_json(request_data.input.file)
            return {"data": work_report.encode().hex(), "status": "Ok"}

        elif label == "work_result":
            work_result = WorkResult.from_json(request_data.input.file)
            return {"data": work_result.encode().hex(), "status": "Ok"}

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

        if label == "assurances_extrinsic":
            assurance, _ = AssurancesExtrinsic.decode_from(data)
            return {"data": assurance.to_json(), "status": "Ok"}

        elif label == "block":
            block, _ = Block.decode_from(data)
            return {"data": block.to_json(), "status": "Ok"}

        elif label == "disputes_extrinsic":
            dispute, _ = DisputesExtrinsic.decode_from(data)
            return {"data": dispute.to_json(), "status": "Ok"}

        elif label == "extrinsic":
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

        elif label == "refine_context":
            context, _ = RefineContext.decode_from(data)
            return {"data": context.to_json(), "status": "Ok"}

        elif label == "tickets_extrinsic":
            ticket, _ = TicketsExtrinsic.decode_from(data)
            return {"data": ticket.to_json(), "status": "Ok"}

        elif label == "work_item":
            work_item, _ = WorkItem.decode_from(data)
            return {"data": work_item.to_json(), "status": "Ok"}

        elif label == "work_package":
            work_package, _ = WorkPackage.decode_from(data)
            return {"data": work_package.to_json(), "status": "Ok"}

        elif label == "work_report":
            work_report, _ = WorkReport.decode_from(data)
            return {"data": work_report.to_json(), "status": "Ok"}

        elif label == "work_result":
            work_result, _ = WorkResult.decode_from(data)
            return {"data": work_result.to_json(), "status": "Ok"}

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        entropy = getattr(request_data.input, 'entropy', None)
        if entropy is None:
            entropy = ByteArray32(bytes(32))

        transition_output = Safrole.transition(test_state, test_block, entropy)
        
        if request_data.output is None:
            return {"ok": None}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = RecentHistory.transition(test_state, test_block, ByteArray32([0]*32))
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Authorization.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Disputes.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Assurances.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Accumulation.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Preimages.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

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
        test_state = GeneralState.from_json(request_data.input.state).to_state()
        transition_output = Statistics.transition(test_state, test_block)
        
        if request_data.output is None:
            return {"result": True}
            
        output_state = GeneralState.from_json(request_data.output.state).to_state()

        if (transition_output == output_state):
            return {"result": True}
        else:
            return {"result": False}
    except Exception as e:
        return JSONResponse(status_code=400, content={"err": str(e)})