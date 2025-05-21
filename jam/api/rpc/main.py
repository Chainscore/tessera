from quart import Quart, request, jsonify
from typing import Any, Dict, Optional
from pydantic import BaseModel
from jam.config import data_stores
from jam.api.rpc.helper_function import (
    best_block_handler,
    finalized_block_handler,
    parent_block_handler,
    state_root_handler,
    statistics_handler,
    service_data_handler,
    service_value_handler,
    service_preimage_handler,
    service_request_handler,
    )
app = Quart(__name__) 
# Following the etherum json rpc api structure
"""
curl https://docs-demo.quiknode.pro/ \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{"method":"eth_getStorageAt","params":["0xc98F11DAAAC76D3ef368fDF54fbbA34FfD951976", "0x2293", "latest"],"id":1,"jsonrpc":"2.0"}'

{"jsonrpc":"2.0","id":1,"result":"0x0000000000000000000000000000000000000000000000000000000000000000"}

"""


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



@app.route("/rpc", methods=["POST"])
async def rpc_handler():
    """
    RPC requests for different methods.
    """
    data = await request.get_json()
    req = RpcRequest(**data)
    method = req.method
    handler = method_map.get(method)

    if not handler:
        return jsonify({
            "jsonrpc": "2.0",
            "id": req.id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"}
        })

    try:
        result = handler(req.params, req.id, data_stores.main_db)
        print(f"Handler result: {result}")
        return jsonify({
            "jsonrpc":"2.0",
            "id":req.id,
            "result":result
        } )
    except Exception as e:
        print(f"Error in handler: {e}")
        return jsonify({
            "jsonrpc":"2.0",
            "id":req.id,
            "error":{"code": -32000, "message": str(e)}
            }
        )

# ...existing code...

if __name__ == "__main__":
    app.run()