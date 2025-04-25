import tempfile
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, Optional
from jam.db.kv import KVStore
from jam.state.state import State
from jam.consensus.grandpa.finality import Finality
from jam.types.block import Block
from jam.types.protocol.core import TimeSlot
from jam.types.header import Header

# Initialize FastAPI with metadata for Swagger UI
app = FastAPI(
    title="Tessera RPC API",
    description="RPC for Tessera node ",
    version="1.0.0",
)

#db path
db_path = tempfile.mkdtemp()

# Initialize store
db = KVStore(db_path)
state = State.genesis()
db_block = Block.load(TimeSlot(0), db)
state.save(db)

# Load the state from the database
db_state = State.load(db)
print("header hash to bytes 32", Header.__hash__(db_block.header).to_bytes(32))
print("header hash", Header.__hash__(db_block.header))
print("hash bytes to hex", Header.__hash__(db_block.header).to_bytes(32).hex())
print("hash arrray", list(Header.__hash__(db_block.header).to_bytes(32)))
# print("Retrieved State:", db_state)
# print("db_path", db.load())

# print("state", state)
# print("block", block)
# print("block stats", state.pi)
# print("block_hash", Header.__hash__(block.header).to_bytes(32), type (Header.__hash__(block.header).to_bytes(32)))

# Following the etherum json rpc api structure
"""
curl https://docs-demo.quiknode.pro/ \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{"method":"eth_getStorageAt","params":["0xc98F11DAAAC76D3ef368fDF54fbbA34FfD951976", "0x2293", "latest"],"id":1,"jsonrpc":"2.0"}'

{"jsonrpc":"2.0","id":1,"result":"0x0000000000000000000000000000000000000000000000000000000000000000"}

"""

# Request model
class RpcRequest(BaseModel):
    method: str
    jsonrpc: str 
    params: Dict[str, Any]
    id: Optional[Any]

# Response models
#block.py
#grandpa.py
class RpcResponse(BaseModel):
    jsonrpc: str
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int]


@app.post("/rpc.tessera", response_model=RpcResponse)
async def rpc_handler(request: RpcRequest):
    """
    RPC requests for different methods.
    """
    method = request.method
    params = request.params

    if method == "bestBlock":
        # Handle bestBlock method        
        return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[
                    Header.__hash__(db_block.header), 
                    int(db_block.header.slot)]
            )
            
    elif method == "finalizedBlock":
    # Handle finalizedBlock method without requiring params
        return RpcResponse(
            jsonrpc="2.0",
            id=request.id,
            result=[
                Header.__hash__(Finality.load_final(db).header),
                int(Finality.load_final(db).header.slot)
            ]
        )
            
    elif method == "parent":
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )
        if len(params):
            if params["Hash"] == Header.__hash__(db_block.header):
                # Return the parent block
                parent_block = Block.load_parent(db_block.header.slot, db)
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    result=[
                        Header.__hash__(parent_block.header), 
                        parent_block.header.slot]
                )
            else:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={"code": -32602, "message": "unexpected error"},
                )
        
    elif method == "stateRoot":
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )
        
        header_hash = params.get("Hash")
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )

        if header_hash == Header.__hash__(db_block.header):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[db_block.header.parent_state_root.encode()],
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )

    elif method == "statistics":   
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )
        
        header_hash = params.get("Hash")
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )

        if header_hash == Header.__hash__(db_block.header):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[db_state.pi.encode()]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )

    # Default case for unrecognized methods
    return RpcResponse(
        jsonrpc="2.0",
        id=request.id,
        error={"code": -32601, "message": "Method not found"},
    )