import asyncio
from jam.api.rpc.api_handlers import dispatch_api_call
from jam.api.rpc.utils import RpcRequest
from jam.api.rpc.websocket import ws_receive, ws_broker
from jam.logging import get_logger
from quart import Quart, websocket, jsonify, request

logger = get_logger("rpc")

rpc = Quart(__name__)

@rpc.route("/rpc", methods=["POST"])
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
    topic = await websocket.receive()  # e.g., client sends: "news"
    task = asyncio.ensure_future(ws_receive())
    try:
        async for message in ws_broker.subscribe(topic):
            await websocket.send(f"[{topic}] {message}")
    finally:
        task.cancel()
        await task


# TODO - Cleanup - remove this upon ws testing
# # Start the splitter in the background
# @rpc.before_serving
# async def startup():
#     rpc.sub_stats = asyncio.create_task(splitter.subscribe_statistics())
#     rpc.sub_service_data = asyncio.create_task(splitter.subscribe_service_data())
#     rpc.sub_service_val = asyncio.create_task(splitter.subscribe_service_value())
#     rpc.sub_service_preimage = asyncio.create_task(splitter.subscribe_service_preimage())
#     rpc.sub_service_request = asyncio.create_task(splitter.subscribe_service_request())
#     rpc.sub_best_block = asyncio.create_task(splitter.subscribe_best_block())
#     rpc.sub_fin_block = asyncio.create_task(splitter.subscribe_finalized_block())
#
# # Clean up the task when shutting down
# @rpc.after_serving
# async def shutdown():
#     rpc.sub_stats.cancel()
#     rpc.sub_stats.cancel()
#     rpc.sub_service_data.cancel()
#     rpc.sub_service_val.cancel()
#     rpc.sub_service_preimage.cancel()
#     rpc.sub_service_request.cancel()
#     rpc.sub_best_block.cancel()
#     rpc.sub_fin_block.cancel()
#     # try:
#     #     await rpc.splitter_task
#     # except asyncio.CancelledError:
#     #     pass
