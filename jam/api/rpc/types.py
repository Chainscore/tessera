"""
RPC Type Definitions

Core types for JSON-RPC 2.0 protocol implementation.
"""

from typing import Any, Optional, Dict
from pydantic import BaseModel


class RpcRequest(BaseModel):
    """JSON-RPC 2.0 Request object."""

    method: str
    jsonrpc: str = "2.0"
    params: list[Any] = []
    id: Optional[Any] = None


class RpcResponse(BaseModel):
    """JSON-RPC 2.0 Response object."""

    jsonrpc: str = "2.0"
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class RpcError(Exception):
    """
    JSON-RPC 2.0 Error.

    Error codes:
    -32700: Parse error
    -32600: Invalid Request
    -32601: Method not found
    -32602: Invalid params
    -32603: Internal error
    -32000 to -32099: Server error

    Custom codes (per JIP-2):
    1: Block unavailable
    2: Work-report unavailable
    3: DA segment unavailable
    0: Other error
    """

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-RPC error object."""
        error = {
            "code": self.code,
            "message": self.message,
        }
        if self.data is not None:
            error["data"] = self.data
        return error
