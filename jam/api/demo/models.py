from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List, Literal


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
    "work_result",
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
    "work_result": "Work result data structure",
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
    file: Dict[str, Any] = Field(..., description="JSON file content to convert to codec format")
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
            "work_result",
        ],
    )

    class Config:
        schema_extra = {"example": {"file": {}, "label": "block"}}


class RequestDataCodec(BaseModel):
    input: InputDataCodec = Field(..., description="Input data for JSON to codec conversion")


# Codec to JSON format
class InputDataJson(BaseModel):
    file: str = Field(
        ...,
        description="Hex-encoded codec data to convert to JSON",
        example="0a1b2c3d4e5f",
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
            "work_result",
        ],
    )

    class Config:
        schema_extra = {"example": {"file": "0a1b2c3d4e5f", "label": "block"}}


class RequestDataJson(BaseModel):
    input: InputDataJson = Field(..., description="Input data for codec to JSON conversion")
