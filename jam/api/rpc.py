import asyncio
import json
import random
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from jam.consensus.grandpa.finality import Finality
from jam.db.kv import KVStore
from jam.state.state import State
from jam.types.block import Block
from jam.types.header import Header
from jam.types.protocol.core import TimeSlot
from jam.types import  U32
from jam.storage.queue import StorageQueue

# Initialize FastAPI with metadata for Swagger UI
app = FastAPI(
    title="Tessera RPC API",
    description=""" RPC for Tessera node  
     ## Documentation Links:  
    - [Tessera API Overview](https://github.com/Chainscore/tessera/blob/feature/rpc_api/jam/api/rpc_doc.md)  
    - [Refered JSON-RPC Specification JIP-2](https://docs.jamcha.in/advanced/rpc/jip2-node-rpc)  
    - Followed formatting and structure of [Ethereum JSON-RPC](https://www.quicknode.com/docs/ethereum)
    
    """,
    version="1.0.0",
)

# db path
db_path = tempfile.mkdtemp()

# Initialize store
db = KVStore(db_path)
state = State.genesis()
db_block = Block.load(TimeSlot(0), db)
state.save(db)
db_state = State.load(db)


# Following the etherum json rpc api structure
"""
curl https://docs-demo.quiknode.pro/ \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{"method":"eth_getStorageAt","params":["0xc98F11DAAAC76D3ef368fDF54fbbA34FfD951976", "0x2293", "latest"],"id":1,"jsonrpc":"2.0"}'

{"jsonrpc":"2.0","id":1,"result":"0x0000000000000000000000000000000000000000000000000000000000000000"}

"""


def best_block_handler(params, request_id):
    print("Best block handler called with params:", params)
    if len(params) != 0:
            return RPCResponse(
                jsonrpc="2.0",
                id=request_id,
                error={"code": -32602, "message": "Invalid parameters: expected no params"},
            )
    return [Header.__hash__(db_block.header), int(db_block.header.slot)]

def finalized_block_handler(params, request_id):
    if len(params) != 0:
            return RPCResponse(
                jsonrpc="2.0",
                id=request_id,
                error={"code": -32602, "message": "Invalid parameters: expected no params"},
            )
    final = Finality.load_final(db)
    return [Header.__hash__(final.header), int(final.header.slot)]

def finalized_block_handler(params, request_id):
    if len(params) != 0:
            return RPCResponse(
                jsonrpc="2.0",
                id=request_id,
                error={"code": -32602, "message": "Invalid parameters: expected no params"},
            )
    final = Finality.load_final(db)
    return [Header.__hash__(final.header), int(final.header.slot)]

def parent(params, request_id):
    if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )   
    
    if len(params):
            ## condition if the time slot is of genesis block
        if block.header.slot == U32(0):
            return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                    "code": -32602,
                    "message": "No parent block available for genesis block",
                },
                )

            ## using state trie function
            ## TODO: Make a rocksdb search function that will fetch block with needed hash. As of now returning current state
            if bytes(params["Hash"]):
                # Return the parent block
                parent_block = Block.load_parent(block.header.slot, db)
                return [ Header.__hash__(parent_block.header), int(parent_block.header.slot) ]

def state_root_handler(params, request_id):
    if len(params) != 1:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={
                "code": -32602,
                "message": "Invalid parameters: expected header_hash",
            },
        )

    header_hash = params.get("Hash")
    if header_hash is None or len(header_hash) != 32:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={
                "code": -32602,
                "message": "Invalid parameters: expected header_hash",
            },
        )
    # TODO: Make a rocksdb search function that will fetch block with needed hash. As of now returning current state
    if bytes(params["Hash"]):
        return [
            StateTrie.root_hash
        ]
    else:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={"code": -32602, "message": "unexpected error"},
        )

def statistics_handler(params, request_id):
     if len(params) != 1:
        return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        header_hash = params.get("Hash")
        if header_hash is None or len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        ## TODO: Make a rocksdb search function that will fetch block with needed hash. 
        # As of now returning current state

        if bytes(params["Hash"]):
            return [State.pi.encode()]
            
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={"code": -32602, "message": "unexpected error"},
            )

def service_data_handler(params, request_id):
    if len(params) != 2:
        return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
            )

        header_hash = params.get("Hash")
        service_id = params.get("ServiceId")
        
        if service_id is None:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                },
            )

        if header_hash is None or len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        #TODO: Using DeltaView to get the service data
        # DeltaView from accounts.py used in State.py

        
        if params["serviceId"]:
            return [state.delta[service_id]]              
                    
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
def service_value_handler(params, request_id):
    if len(params) or not(params) != 3:
        return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
             )

        header_hash = params.get("Hash")
        service_id = params.get("ServiceId")
        blob = params.get("Blob")
        
        if header_hash is None or len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )
        
        if service_id is None:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                },
            )

        if blob is None:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected Blob",
                },
            )
        blob_bytes = bytes(blob)
        blob_key = ByteArray32(blob_bytes)
   
        def service_storage()-> StorageView:
            return StorageView(service_id, main_db, StateTrie())

        if bytes(params["Hash"]) and params["serviceId"] and params["Blob"] :
                ##TODO: resolve this correctly
            return [service_storage()[ByteArray32(blob_key)]]
            
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={"code": -32602, "message": "unexpected error"},
            )

def service_preimage_handler(params, request_id):
    if params is None or len(params) != 2:
        return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
            )

        header_hash = params.get("Hash")
        service_id = params.get("ServiceId")
        blob = params.get("Blob")

        
        if header_hash is None or len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )
        
        if service_id is None:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                },
            )
        if blob is None:
            return RpcResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected Blob",
                },
            )
        blob_bytes = bytes(blob)
        blob_key = ByteArray32(blob_bytes)
   
        def service_preimage()-> PreImageView:
            return PreImageView(service_id, main_db, StateTrie())
        
        #TODO: check if service id is in the state 
        if bytes(params["Hash"]) and params["serviceId"] :
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id,
                result=[service_preimage()[blob_key]]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
    
def service_request_handler(params, request_id):
    if len(params) != 4:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={
                "code": -32602,
                "message": "Invalid parameters: expected header_hash and ServiceId",
            },
        )

    header_hash = params.get("Hash")
    service_id = params.get("ServiceId")
    hash = params.get("Hash")
    preimage_len = params.get("u32")

    if header_hash is None or len(header_hash) != 32:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={
                "code": -32602,
                "message": "Invalid parameters: expected header_hash",
            },
        )

    if service_id is None:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={
                "code": -32602,
                "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
            },
        )

    if hash is None:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={
                "code": -32602,
                "message": "Invalid parameters: expected hash",
            },
        )

    if preimage_len is None:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={
                "code": -32602,
                "message": "Invalid parameters: expected preimage_len",
            },
        )

    def service_lookup() -> TimestampsView:
        return TimestampsView(service_id, main_db, StateTrie())

    # TODO: check if service id is in the state
    if params["Hash"] and params["u32"]:
        return [service_lookup()[LookupTable(hash, preimage_len)]]
    else:
        return RpcResponse(
            jsonrpc="2.0",
            id=request_id,
            error={"code": -32602, "message": "unexpected error"},
        )

method_map = {
    "bestBlock": best_block_handler,
    "finalizedBlock": finalized_block_handler,
    "parent": parent_block_handler,
    "stateRoot": state_root_handler,
    "statistics": statistics_handler,
    "serviceData" : service_data_handler,
    "serviceValue" : service_value_handler,
    "servicePreimage" : service_preimage_handler,
    "serviceRequest" : service_request_handler,
    "beefyRoot" : beefy_root_handler,
    "submitPreimage" : submit_preimage_handler,
}

# Request model
class RpcRequest(BaseModel):
    method: str
    jsonrpc: str
    params: Dict[str, Any]
    id: Optional[Any]

    class Config:
        json_schema_extra = {
            "example": {
                "method": "statistics",
                "jsonrpc": "2.0",
                "params": {
                    "Hash": [9, 22, 47, 0, 129, 231, 187, 27, 132, 92, 215, 134, 177, 181, 78, 139, 163, 206, 87, 173, 138, 231, 16, 253, 5, 145, 172, 130, 208, 197, 4, 223]
                },
                "id": 1,
            }
        }

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
    handler = method_map.get(method)

    if not handler:
        return RpcResponse(
            jsonrpc="2.0",
            id=request.id,
            error={"code": -32601, "message": f"Method '{method}' not found"}
        )

    try:
        result = handler(request.params, request.id)
        print(f"Handler result: {result}")
        return RpcResponse(
            jsonrpc="2.0",
            id=request.id,
            result=result
        )
    except Exception as e:
        print(f"Error in handler: {e}")
        return RpcResponse(
            jsonrpc="2.0",
            id=request.id,
            error={"code": -32000, "message": str(e)}
        )