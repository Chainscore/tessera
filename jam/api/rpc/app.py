import asyncio
import json
from jam.api.rpc.broker import broker
from jam.api.rpc.api_handlers import dispatch_api_call
from jam.api.rpc.utils import RpcRequest
from jam.api.rpc.websocket import ws_receive, ws_broker
from jam.logging import get_logger
from quart import Quart, websocket, jsonify, request
import jam.consensus.grandpa.finality as finality

logger = get_logger("rpc")

rpc = Quart(__name__)

logger.info( "RPC server is starting up" )

@rpc.route("/", methods=["POST"])
async def rpc_handler():
    """
    RPC requests for different methods.
    """
    data = await request.get_json()
    req = RpcRequest(**data)

    try:
        result = dispatch_api_call(req.method, req.params)
        return jsonify({
            "jsonrpc":"2.0",
            "id":req.id,
            "result":result
        } )
    except Exception as e:
        logger.error("Error serving API request", error=e)
        return jsonify({
            "jsonrpc":"2.0",
            "id":req.id,
            "error":{"code": -32000, "message": str(e)}
            }
        )

@rpc.websocket("/ws")
async def ws():
    # 1) client sends topic name, e.g. "news"
    topic = await websocket.receive()
    # 2) now push every message for that topic, forever
    async for msg in broker.subscribe(topic):
        # wrap & JSON-serialize
        # await websocket.send(json.dumps({"topic": topic, "data": msg}))
        await websocket.send(json.dumps(msg))


