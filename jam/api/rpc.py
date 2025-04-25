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
block = Block.load(TimeSlot(0), db)
print("state", state)
print("block", block)
print("block stats", state.pi)
print("block_hash", Header.__hash__(block.header).to_bytes(32), type (Header.__hash__(block.header).to_bytes(32)))

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


@app.post("/rpc.tessera", response_model=RpcRequest)
async def rpc_handler(request: RpcRequest):
    """
    RPC requests for different methods.
    """
    method = request.method
    params = request.params

#block -> block.encode()
    
    if method == "bestBlock":
        # Handle bestBlock method
        # Takes no arguments
        if len(params):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[Header.__hash__(block.header).to_bytes(32), block.header.slot]
            )
            
    elif method == "finalizedBlock":
        if len(params):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[Header.__hash__(Finality.load_final(db).header), Finality.load_final(db).header.slot]
            )
    elif method == "parent":
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )
        if len(params):
            if(params["Hash"] == Header.__hash__(block.header).to_bytes(32)):
                # Return the parent block
                parent_block = Block.load_parent(block.header.slot, db)
                
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    result=[Header.__hash__(parent_block.header), parent_block.header.slot]
                )
            else:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={"code": -32602, "message": "unexpected error"},
                )
        
    elif method == "stateRoot":
        # Handle stateRoot method
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )
        
        # Extract header_hash from params
        header_hash = params.get("Hash")
        
        # Validate header_hash
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )

        # Fetch latest state from db
        # db_state = state.load(kv)

        # Return the state root
        if(header_hash == Header.__hash__(block.header).to_bytes(32)):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[block.header.parent_state_root.encode()],
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )

    elif method == "statistics":   
        # Handle parent method
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )
         # Extract header_hash from params
        header_hash = params.get("Hash")

        # Validate header_hash
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Invalid parameters: expected header_hash"},
            )

        # Return the state root
        if(header_hash == Header.__hash__(block.header).to_bytes(32)):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[state.pi.encode()]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
    
