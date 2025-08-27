import asyncio
import json
from jam.api.rpc.broker import broker
from jam.api.rpc.api_handlers import dispatch_api_call
from jam.api.rpc.utils import RpcRequest
from jam.api.rpc.websocket import ws_receive, ws_broker
from jam.logging import get_logger
from quart import Quart, websocket, jsonify, request
import jam.finality.finality as Finality
import itertools
from tsrkit_types import U32


def _json_default(val):
    # 1) U32 → int
    if isinstance(val, U32):
        return int(val)
    # 2) anything iterable (Bytes, TypedVector, etc) → list(val)
    try:
        return list(val)
    except Exception:
        pass
    return str(val)


logger = get_logger("rpc")

rpc = Quart(__name__)

logger.info("RPC server is starting up")
# subscription ID's setup
# increment sub id at every connection
_sub_id_counter = itertools.count(1)
sub_id = next(_sub_id_counter)


@rpc.route("/", methods=["POST"])
async def rpc_handler():
    """
    RPC requests for different methods.
    """
    data = await request.get_json()
    req = RpcRequest(**data)

    try:
        result = dispatch_api_call(req.method, req.params)
        return jsonify({"jsonrpc": "2.0", "id": req.id, "result": result})
    except Exception as e:
        logger.error("Error serving API request", error=e)
        return jsonify(
            {
                "jsonrpc": "2.0",
                "id": req.id,
                "error": {"code": -32000, "message": str(e)},
            }
        )


@rpc.websocket("/")
async def ws():
    raw = await websocket.receive()
    # increment sub id at every connection
    sub_id = next(_sub_id_counter)

    req = json.loads(raw)

    method = req.get("method")
    params = req.get("params", [])
    req_id = req.get("id")

    async for msg in broker.subscribe(method):
        # wrap & JSON-serialize

        from jam.settings import settings

        final = Finality.load_final(settings.main_db)
        # await websocket.send(json.dumps({"id":1, "jsonrpc": "2.0", "result":sub_id}))

        # special handling for subscribeBestBlock and subscribeFinalizedBlock
        if method == "subscribeBestBlock" or method == "subscribeFinalizedBlock":
            await websocket.send(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": {"subscription": sub_id, "result": msg},
                    },
                    default=_json_default,
                )
            )
        else:
            await websocket.send(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": {
                            "subscription": sub_id,
                            "result": {
                                "header_hash": final.header.hash(),
                                "slot": int(final.header.slot),
                                "value": msg,
                            },
                        },
                    },
                    default=_json_default,
                )
            )
