from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from tsrkit_types import Codable


class RpcRequest(BaseModel):
    method: str
    jsonrpc: str
    params: list[Any]
    id: Optional[Any]

    class Config:
        json_schema_extra = {
            "example": {
                "method": "statistics",
                "jsonrpc": "2.0",
                "params": [
                    [9, 22, 47, 0, 129, 231, 187, 27, 132, 92, 215, 134, 177, 181, 78, 139, 163, 206, 87, 173, 138, 231, 16, 253, 5, 145, 172, 130, 208, 197, 4, 223]
                ],
                "id": 1,
            }
        }

class RpcResponse(BaseModel):
    jsonrpc: str
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int]

def parse_data(data_types: list[Type[Codable]], data: list) -> list[Codable]:
    ret = []
    for i, d in enumerate(data):
        ret.append(data_types[i](d))


    return ret
