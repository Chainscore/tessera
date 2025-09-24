import asyncio
import json
from jam.api.rpc.broker import broker
from jam.api.rpc.api_handlers import dispatch_api_call
from jam.api.rpc.utils import RpcRequest
from jam.log_setup import node_logger as logger
from quart import Quart, websocket, jsonify, request
import itertools
from tsrkit_types import U32
from .ws_handlers import dispatch_ws_call


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



rpc = Quart(__name__)

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

_sub_id_counter = itertools.count(1)

SUBSCRIPTIONS = {
    "subscribeSyncStatus":  lambda params: "subscribeSyncStatus",
    "subscribeFinalizedBlock": lambda params: "subscribeFinalizedBlock",
    "subscribeServiceRequest": lambda params:(
        f"subscribeServiceRequest:{params[0]}:{params[1]}:{params[2]}:{params[3]}"
    ),
    "subscribeServiceValue": lambda params:(
        f"subscribeServiceValue:{params[0]}:{params[1]}:{params[2]}"
    ),
    "subscribeBestBlock": lambda params: "subscribeBestBlock"
}

@rpc.websocket("/")
async def ws():
    # active subscriptions for this connection: sub_id -> task
    subs: dict[int, asyncio.Task] = {}
    topics: dict[int, str] = {}

    async def start_subscription(method: str, params, req_id):
        topic = SUBSCRIPTIONS[method](params)

        sub_id = next(_sub_id_counter)

        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": sub_id
        }))

        async def pump(t=topic, sid=sub_id, notify_method=method):
            try:
                async for msg in broker.subscribe(t):
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "method": notify_method,
                        "params": {
                            "subscription": sid,
                            "result": msg
                        }
                    }))
            except Exception:
                pass

        subs[sub_id] = asyncio.create_task(pump())
        topics[sub_id] = topic

    try:
        while True:
            raw = await websocket.receive()
            if raw is None:
                break

            req = json.loads(raw)
            method = req.get("method")
            params = req.get("params", [])
            req_id = req.get("id")

            if method in SUBSCRIPTIONS:
                await start_subscription(method, params, req_id)
                continue

            # unsubscribe just this stream using id
            if method == "unsubscribeSyncStatus" or method == "unsubscribeFinalizedBlock" or method == "unsubscribeServiceRequest" or method == "unsubscribeServiceValue":
                ok = False
                if params:  # expect [sub_id]
                    sid = params[0]
                    task = subs.pop(sid, None)
                    topic = topics.pop(sid, None)
                    broker.topics.pop(topic, None)
                    broker.last_publish.pop(topic, None)
                    if task:
                        task.cancel()
                        ok = True
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": ok
                }))
                continue

            # normal request/response
            result = dispatch_ws_call(method, params)

            if result is not None:
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }))
            else:
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": None
                }))
    finally:
        # remove all subscription tasks on disconnect
        for t in subs.values():
            t.cancel()
