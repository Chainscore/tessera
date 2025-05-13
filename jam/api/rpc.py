import asyncio
import json
import random
from datetime import datetime
from typing import Any, Dict, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from jam.consensus.grandpa.finality import Finality
from jam.types.block import Block
from jam.types.header import Header
from jam.types import  U32
from jam.storage.queue import StorageQueue
from jam.config.data_stores import main_db #swithing to main_db
from jam.state.merkle import StateTrie
from jam.state.state import State
from jam.types.protocol.core import ServiceId

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

db = main_db
# Get state and block from db
block = Block.load(State.tau, db)


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


# Response models
# block.py
# grandpa.py
class RpcResponse(BaseModel):
    jsonrpc: str
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int]


@app.post("/rpc.tessera", response_model=RpcResponse)
async def rpc_handler(request: RpcRequest):
    """z
    RPC requests for different methods.
    """
    method = request.method
    params = request.params
##---------------------------------------------------------------------------

    if method == "bestBlock":
        # Handle bestBlock method
        return RpcResponse(
            jsonrpc="2.0",
            id=request.id,
            result=[Header.__hash__(block.header), int(block.header.slot)],
        )

##----------------------------------------------------------------------------

    elif method == "finalizedBlock":
        # Handle finalizedBlock method without requiring params
        return RpcResponse(
            jsonrpc="2.0",
            id=request.id,
            result=[
                Header.__hash__(Finality.load_final(db).header),
                int(Finality.load_final(db).header.slot),
            ],
        )

##---------------------------------------------------------------------------
    elif method == "parent":
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

                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    result=[
                        Header.__hash__(parent_block.header),
                        int(parent_block.header.slot),
                    ],
                )
            else:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={"code": -32602, "message": "unexpected error"},
                )

##-------------------------------------------------------------------------------------

    elif method == "stateRoot":
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        header_hash = params.get("Hash")
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )
        ## TODO: Make a rocksdb search function that will fetch block with needed hash. As of now returning current state
        if bytes(params["Hash"]):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[
                        StateTrie.root_hash,
                    ],
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )

##--------------------------------------------------------------------------------

    elif method == "statistics":
        if len(params) != 1:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        header_hash = params.get("Hash")
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        ## TODO: Make a rocksdb search function that will fetch block with needed hash. As of now returning current state

        if bytes(params["Hash"]):
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id, 
                result=[State.pi.encode()]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
##------------------------------------------------------------------------
    elif method == "serviceData":
        if len(params) != 2:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
            )

        header_hash = params.get("Hash")
        service_id = params.get("ServiceId")
        if not (0 <= service_id <= 2**32 - 1):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                },
            )

        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        #TODO: check if service id is in the state 
        if bytes(params["Hash"]) == hash(block.header).to_bytes(32) :
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id, 
                result=[]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
    elif method == "serviceValue":
        if len(params) != 3:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
            )

        header_hash = params.get("Hash")
        service_id = params.get("ServiceId")
        blob = params.get("Blob")
        
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        #TODO: check if service id is in the state 
        if bytes(params["Hash"]) == hash(block.header).to_bytes(32) :
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id,
                ##TODO: resolve this correctly
                result=[State.delta]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )

    elif method == "servicePreimage":
        if len(params) != 2:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash and ServiceId",
                },
            )

        header_hash = params.get("Hash")
        service_id = params.get("ServiceId")
        header_hash = params.get("Hash")

        
        if len(header_hash) != 32:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": "Invalid parameters: expected header_hash",
                },
            )

        #TODO: check if service id is in the state 
        if bytes(params["Hash"]) == hash(block.header).to_bytes(32) :
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id, 
                result=[state.delta]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
    elif method == "serviceRequest":
            if len(params) != 4:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid parameters: expected header_hash and ServiceId",
                    },
                )

            header_hash = params.get("Hash")
            service_id = params.get("ServiceId")
            header_hash = params.get("Hash")
            preimage_len = params.get("u32")
            
            if not (0 <= service_id <= 2**32 - 1):
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid parameters: expected ServiceId as single numeric item between 0 and 2^(32)−1 inclusive",
                    },
                )

            if len(header_hash) != 32:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid parameters: expected header_hash",
                    },
                )

            #TODO: check if service id is in the state 
            if bytes(params["Hash"]) == hash(block.header).to_bytes(32) :
                return RpcResponse(
                    jsonrpc="2.0", 
                    id=request.id, 
                    result=[state.delta]
                )
            else:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={"code": -32602, "message": "unexpected error"},
                )
    elif method == "beefyRoot":
            if len(params) != 1:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid parameters: expected header_hash and ServiceId",
                    },
                )

            header_hash = params.get("Hash")

        
            if len(header_hash) != 32:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid parameters: expected header_hash",
                    },
                )

            #TODO: check if service id is in the state 
            if bytes(params["Hash"]) == hash(block.header).to_bytes(32) :
                return RpcResponse(
                    jsonrpc="2.0", 
                    id=request.id, 
                    result=[state.delta]
                )
            else:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={"code": -32602, "message": "unexpected error"},
                )
    elif method == "submitPreimage":
            if len(params) != 1:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid parameters: expected header_hash and ServiceId",
                    },
                )

            header_hash = params.get("Hash")

        
            if len(header_hash) != 32:
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid parameters: expected header_hash",
                    },
                )

            #TODO: check if service id is in the state 
            if bytes(params["Hash"]) == hash(block.header).to_bytes(32) :
                return RpcResponse(
                    jsonrpc="2.0", 
                    id=request.id, 
                    result=[state.delta]
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



class SubscriptionManager:
    def __init__(self):
        self.active_connections = {}
        self.subscriptions = {}
        # Track the last known position in the updates queue
        self.last_queue_position = 0
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = set()
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            # Remove all subscriptions for this client
            for method in self.active_connections[websocket]:
                if method in self.subscriptions and websocket in self.subscriptions[method]:
                    self.subscriptions[method].remove(websocket)
            del self.active_connections[websocket]
    
    def subscribe(self, websocket: WebSocket, method: str):
        if method not in self.subscriptions:
            self.subscriptions[method] = set()
        self.subscriptions[method].add(websocket)
        self.active_connections[websocket].add(method)
    
    def unsubscribe(self, websocket: WebSocket, method: str):
        if method not in self.subscriptions or websocket not in self.subscriptions[method]:
            return False
        self.subscriptions[method].remove(websocket)
        self.active_connections[websocket].remove(method)
        return True
    
    async def broadcast(self, method, message):
        if method in self.subscriptions:
            disconnected_websockets = []
            for websocket in self.subscriptions[method]:
                try:
                    response = {
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": {"subscription": method, "result": message}
                    }
                    await websocket.send_text(json.dumps(response))
                except Exception:
                    disconnected_websockets.append(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket)

# Create a global instance of the subscription manager
#TODO: Can this be used as a global
manager = SubscriptionManager()

# Create a global updates queue for tracking database changes
updates_queue = StorageQueue("db_updates")

@app.websocket("/rpc.tessera")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for client to send subscription requests
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                # Handle subscription requests
                if "method" in request and "id" in request:
                    method = request["method"]
                    if method == "subscribeStatistics":
                        # Subscribe to statistics
                        manager.subscribe(websocket, "subscribeStatistics")
                        # Send immediate response with current data
                        response = RpcResponse(
                            jsonrpc="2.0",
                            id=request["id"],
                            result=[state.pi.encode()]
                        )
                        await websocket.send_text(response.json())
                    elif method == "unsubscribe" and "params" in request:
                        # Unsubscribe from a specific method
                        unsub_method = request["params"]["method"]
                        success = manager.unsubscribe(websocket, unsub_method)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "result": {"success": success},
                        }
                        await websocket.send_text(json.dumps(response))
                    else:
                        # Unknown method
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {"code": -32601, "message": "Method not found"},
                            "id": request["id"],
                        }
                        await websocket.send_text(json.dumps(error_response))
            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                }
                await websocket.send_text(json.dumps(error_response))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def get_blockchain_statistics():
    # Generate random blockchain statistics
    block_height = random.randint(12000, 13000)
    transactions = random.randint(5000, 6000)
    hash_rate = f"{random.uniform(10.0, 15.0):.1f} TH/s"
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    return {
        "blockHeight": block_height,
        "transactions": transactions,
        "hashRate": hash_rate,
        "timestamp": timestamp,
    }

@app.on_event("startup")
async def start_broadcasters():
    # Start the queue polling task
    asyncio.create_task(poll_updates_queue())


async def poll_updates_queue(interval=1):
    """
    updates queue for new entries and broadcast them to subscribers.
    """
    global manager, updates_queue
    
    while True:
        try:
            # Get queue metadata to check if there are new items
            metadata = updates_queue.metadata(db)
            current_tail = int(metadata.tail) if metadata else 0
            
            # If there are new entries, process them
            if current_tail > manager.last_queue_position:
                # Get  new entries since last position
                count = current_tail - manager.last_queue_position
                new_entries = updates_queue.get(db, count, manager.last_queue_position)
                
                if new_entries:
                    # Parse the entries
                    updates = []
                    for entry in new_entries:
                        try:
                             # Parse the entry into `update_data`
                             update_data = entry.decode("utf-8")  # Example: decoding bytes to string
                             updates.append(update_data) 
                        except:
                            print(f"Error parsing update: {entry}")
                    
                    # If we have valid updates, broadcast them
                    if updates:
                        # stats = get_blockchain_statistics()
                        stats["updates"] = updates
                        await manager.broadcast("subscribeStatistics", stats)
                
                # Update our position in the queue
                manager.last_queue_position = current_tail
                
        except Exception as e:
            print(f"[poll_updates_queue] Error: {e}")
        
        # Wait before next poll
        await asyncio.sleep(interval)

