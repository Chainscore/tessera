import json
from enum import Enum
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union, Literal
from jam.report.state import Reporting
from jam.accumulation.accumulation import Accumulation
from jam.assurances.assurances import Assurances
from jam.authorization.authorization import Authorization
from jam.disputes.disputes import Disputes
from jam.statistics.statistics import Statistics
from jam.types import Boolean
from jam.types.base.sequences.bytes import ByteArray32
from jam.api.api_functions import (
    export_json_to_codec,
    export_cases_types,
    export_codec_to_json,
    export_safrole,
    export_safrole_keyval,
    export_shuffle_validate,
    export_recent_history,
    export_authorization,
    export_assurances,
    export_disputes,
    export_report,
    export_accumulate,
    export_preimages,
)
from jam.api.response_models import (
    SuccessResponse,
    ErrorResponse,
    ConversionSuccessResponse,
    RequestData,
    RequestDataJson,
    RequestDataCodec,
    RequestDataShuffle,
    RequestDataTypes,
    TYPES_ENUM
)

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


@app.get("/api/v1/types/validate", 
         response_model=RequestDataTypes,
         tags=["Types"],
         summary="List all available types",
         description="Returns an overview of all available types in the system",
         responses={
             200: {"description": "List of available types"}
         })
async def list_all_types():
     return export_cases_types()

@app.post('/api/v1/types/json_to_codec',
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
async def json_to_codec(request_data: RequestDataCodec,
        type_id : str = Query("assurances_extrinsic", enum = TYPES_ENUM)):
    
    return export_json_to_codec(request_data, type_id)

@app.post('/api/v1/types/codec_to_json',
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
async def codec_to_json(request_data: RequestDataJson, type_id : str = Query("assurances_extrinsic", enum = TYPES_ENUM)):
    
    return export_codec_to_json(request_data, type_id)


@app.post("/api/v1/safrole/validate",
          tags=["State Transitions"],
          summary="Validate Safrole state transition",
          description="Validates state transition according to Safrole consensus rules",
          responses={
              200: {"description": "Validation succeeded", "model": Dict[str, None]},
              400: {"description": "Validation failed", "model": ErrorResponse}
          })
async def safrole(request_data: RequestData,    
type_id : str = Query("non_keyval", enum = [
        "non_keyval",
        "keyval"
    ])):
    return export_safrole(request_data, type_id)

@app.post("/api/v1/safrole/validate_keyval")
async def safrole_keyval(request_data: RequestData):
    return export_safrole_keyval(request_data)

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
    return export_shuffle_validate(request_data)

@app.post("/api/v1/recent_history/validate",
          tags=["State Transitions"],
          summary="Validate Recent History state transition",
          description="Validates state transition according to Recent History rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def recent_history(request_data: RequestData):
    return export_recent_history(request_data)

@app.post("/api/v1/authorization/validate",
          tags=["State Transitions"],
          summary="Validate Authorization state transition",
          description="Validates state transition according to Authorization rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def authorization(request_data: RequestData):
    return export_authorization(request_data)

@app.post("/api/v1/disputes/validate",
          tags=["State Transitions"],
          summary="Validate Disputes state transition",
          description="Validates state transition according to Disputes resolution rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def disputes(request_data: RequestData):
    return export_disputes(request_data)

@app.post("/api/v1/assurances/validate",
          tags=["State Transitions"],
          summary="Validate Assurances state transition",
          description="Validates state transition according to Assurances rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def assurances(request_data: RequestData):
    return export_assurances(request_data)


@app.post("/api/v1/report/validate",
          tags=["State Transitions"],
          summary="Validate Report state transition",
          description="Validates state transition according to Report rules (incomplete)",
          responses={
              200: {"description": "Validation result"},
              400: {"description": "Validation failed", "model": ErrorResponse}
          })
async def report(request_data: RequestData):
    return export_report(request_data)

@app.post("/api/v1/accumulate/validate",
          tags=["State Transitions"],
          summary="Validate Accumulation state transition",
          description="Validates state transition according to Accumulation rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def accumulate(request_data: RequestData):
    return export_accumulate(request_data)
    
@app.post("/api/v1/preimages/validate",
          tags=["State Transitions"],
          summary="Validate Preimages state transition",
          description="Validates state transition according to Preimages rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def preimages(request_data: RequestData):
    return export_preimages(request_data)


@app.post("/api/v1/statistics/validate",
          tags=["State Transitions"],
          summary="Validate Statistics state transition",
          description="Validates state transition according to Statistics rules",
          responses={
              200: {"description": "Validation result", "model": Union[Dict[str, bool], ErrorResponse]}
          })
async def statistics(request_data: RequestData):
    return export_statistics(request_data)