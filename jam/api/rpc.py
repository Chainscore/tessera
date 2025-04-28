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


# Initialize FastAPI with metadata for Swagger UI
app = FastAPI(
    title="Tessera RPC API",
    description="RPC for Tessera node ",
    version="1.0.0",
)

# db path
db_path = tempfile.mkdtemp()

# Initialize store
db = KVStore(db_path)
state = State.genesis()
db_block = Block.load(TimeSlot(0), db)
state.save(db)
# print(state.load(db, "0x0023000000000000478648cd19b4f812f897a26976ecf312eac28508b4368d0c"))
# Load the state from the database
db_state = State.load(db)

# print("header hash to bytes 32", Header.__hash__(db_block.header).to_bytes(32))
# print("header hash", Header.__hash__(db_block.header))
# print("hash bytes to hex", Header.__hash__(db_block.header).to_bytes(32).hex())
# print("hash arrray", list(Header.__hash__(db_block.header).to_bytes(32)))
# hash_array = list(Header.__hash__(db_block.header).to_bytes(32))
# hash_bytes = bytes(hash_array)
# print(hash_bytes)
# print("db_block.header.slot", db_state)

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
# block.py
# grandpa.py
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
            result=[Header.__hash__(db_block.header), int(db_block.header.slot)],
        )

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

            if db_block.header.slot == U32(0):
                return RpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                    "code": -32602,
                    "message": "No parent block available for genesis block",
                },
                )

            if bytes(params["Hash"]) == Header.__hash__(db_block.header).to_bytes(32):
                # Return the parent block
                parent_block = Block.load_parent(db_block.header.slot, db)
                print("parent_block.header.slot", parent_block.header.slot)

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
        
        if bytes(params["Hash"]) == Header.__hash__(db_block.header).to_bytes(32):
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=[
                    bytes(db_block.header.parent_state_root).hex(),
                    ],
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

        if bytes(params["Hash"]) == Header.__hash__(db_block.header).to_bytes(32):
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
        if bytes(params["Hash"]) == Header.__hash__(db_block.header).to_bytes(32) :
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id, 
                result=[db_state.delta]
            )
        else:
            return RpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "unexpected error"},
            )
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
        if bytes(params["Hash"]) == Header.__hash__(db_block.header).to_bytes(32) :
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id, 
                result=[db_state.delta]
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
        if bytes(params["Hash"]) == Header.__hash__(db_block.header).to_bytes(32) :
            return RpcResponse(
                jsonrpc="2.0", 
                id=request.id, 
                result=[db_state.delta]
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
            if bytes(params["Hash"]) == Header.__hash__(db_block.header).to_bytes(32) :
                return RpcResponse(
                    jsonrpc="2.0", 
                    id=request.id, 
                    result=[db_state.delta]
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
        self.connections: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            del self.connections[websocket]

    def subscribe(self, websocket: WebSocket, method: str):
        if websocket in self.connections:
            self.connections[websocket].add(method)
            return True
        return False

    def unsubscribe(self, websocket: WebSocket, method: str):
        if websocket in self.connections and method in self.connections[websocket]:
            self.connections[websocket].remove(method)
            return True
        return False

    async def broadcast(self, method: str, data: dict):
        message = {"jsonrpc": "2.0", "method": method, "result": data}

        for websocket, subscriptions in self.connections.items():
            if method in subscriptions:
                await websocket.send_text(json.dumps(message))


manager = SubscriptionManager()


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
                        response = {
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "result": [db_state.pi.encode()],
                        }
                        await websocket.send_text(json.dumps(response))

                    elif method == "subscribeTransactions":
                        # Subscribe to transaction statistics
                        manager.subscribe(websocket, "subscribeTransactions")

                        # Send immediate response with current data
                        current_stats = get_transaction_statistics()
                        response = {
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "result": current_stats,
                        }
                        await websocket.send_text(json.dumps(response))

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


@app.on_event("startup")
async def start_broadcasters():
    asyncio.create_task(statistics_broadcaster())
    asyncio.create_task(transactions_broadcaster())


async def statistics_broadcaster():
    while True:
        stats = get_blockchain_statistics()
        await manager.broadcast("subscribeStatistics", stats)
        await asyncio.sleep(5)


async def transactions_broadcaster():
    while True:
        stats = get_transaction_statistics()
        await manager.broadcast("subscribeTransactions", stats)
        await asyncio.sleep(3)


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


def get_transaction_statistics():
    # Generate random transaction statistics
    pending_txs = random.randint(100, 500)
    avg_fee = random.uniform(0.001, 0.01)
    avg_confirmation_time = random.uniform(20, 60)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    return {
        "pendingTransactions": pending_txs,
        "averageFee": f"{avg_fee:.5f}",
        "averageConfirmationTime": f"{avg_confirmation_time:.2f} seconds",
        "timestamp": timestamp,
    }
