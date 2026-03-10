"""
WebSocket Route

WebSocket JSON-RPC endpoint handler with subscription support.
"""

import asyncio
import json
import uuid
from quart import Quart, websocket
from typing import TYPE_CHECKING
import structlog

from jam.api.rpc.types import RpcRequest
from jam.api.rpc.utils.serialization import json_default

if TYPE_CHECKING:
    from jam.api.rpc.dispatcher import Dispatcher
    from jam.api.rpc.broker import Broker
    from jam.api.rpc.subscriptions.manager import SubscriptionManager


class WebSocketRoute:
    """
    WebSocket JSON-RPC endpoint with subscription support.

    Handles:
    - Regular JSON-RPC requests (same as HTTP)
    - Subscription creation
    - Subscription updates (pushed to client)
    - Unsubscription
    """

    def __init__(
        self,
        app: Quart,
        dispatcher: "Dispatcher",
        broker: "Broker",
        subscription_manager: "SubscriptionManager",
    ):
        self.app = app
        self.dispatcher = dispatcher
        self.broker = broker
        self.sub_manager = subscription_manager
        self.logger = structlog.get_logger("rpc")
        self._register()

    def _register(self):
        """Register WebSocket route with Quart."""

        @self.app.websocket("/")
        async def ws_handler():
            """Handle WebSocket connections."""
            connection_id = str(uuid.uuid4())[:8]

            self.logger.info("websocket_connected", connection_id=connection_id)

            # Track subscriptions for this connection
            # sub_id -> {"method": ..., "params": ..., "task": ...}
            subscription_tasks: dict[int, dict] = {}

            try:
                while True:
                    # Receive message
                    raw = await websocket.receive()

                    if raw is None:
                        break

                    # Parse JSON
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        await self._send_error(None, -32700, "Parse error")
                        continue

                    # Create request
                    req_id = data.get("id")
                    method = data.get("method")
                    params = data.get("params", [])

                    self.logger.debug(
                        "websocket_message", connection_id=connection_id, method=method, id=req_id
                    )

                    # Handle subscription
                    if self.dispatcher.is_subscription_method(method):
                        await self._handle_subscription(
                            connection_id, req_id, method, params, subscription_tasks
                        )
                        continue

                    # Handle unsubscription
                    if self.dispatcher.is_unsubscribe_method(method):
                        await self._handle_unsubscription(
                            req_id, method, params, subscription_tasks
                        )
                        continue

                    # Regular request
                    await self._handle_request(req_id, method, params)

            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.logger.error(
                    "websocket_error", connection_id=connection_id, error=str(e), exc_info=True
                )
            finally:
                # Cleanup all subscriptions for this connection
                for sub_info in subscription_tasks.values():
                    sub_info["task"].cancel()

                self.sub_manager.cleanup_connection(connection_id)

                self.logger.info(
                    "websocket_disconnected",
                    connection_id=connection_id,
                    subscriptions_cleaned=len(subscription_tasks),
                )

    async def _handle_subscription(
        self, connection_id: str, req_id: any, method: str, params: list, subscription_tasks: dict
    ):
        """Handle subscription creation."""
        try:
            # Create subscription (returns sub_id only now)
            sub_id = self.sub_manager.create_subscription(method, params, connection_id)

            # Send subscription confirmation
            await self._send_result(req_id, sub_id)

            # Start pumping messages (pass method and params, broker generates topic)
            task = asyncio.create_task(self._pump_messages(sub_id, method, params))
            subscription_tasks[sub_id] = {"method": method, "params": params, "task": task}

            # Send initial data
            initial_data = self.dispatcher.get_initial_subscription_data(method, params)
            if initial_data is not None:
                await self._send_notification(method, sub_id, initial_data)

                # Track message in subscription tracker
                self.sub_manager.record_message(sub_id)

        except Exception as e:
            self.logger.error("subscription_error", method=method, error=str(e), exc_info=True)
            await self._send_error(req_id, -32603, "Internal error")

    async def _handle_unsubscription(
        self, req_id: any, method: str, params: list, subscription_tasks: dict
    ):
        """Handle unsubscription."""
        try:
            if not params or not isinstance(params, list):
                await self._send_result(req_id, False)
                return

            sub_id = params[0]

            # Cancel pump task
            sub_info = subscription_tasks.pop(sub_id, None)
            if sub_info:
                sub_info["task"].cancel()

            # Remove subscription
            success = self.sub_manager.unsubscribe(sub_id)

            await self._send_result(req_id, success)

        except Exception as e:
            self.logger.error("unsubscribe_error", error=str(e))
            await self._send_result(req_id, False)

    async def _handle_request(self, req_id: any, method: str, params: list):
        """Handle regular JSON-RPC request."""
        try:
            req = RpcRequest(method=method, params=params, id=req_id)
            response = await self.dispatcher.dispatch(req)

            await self._send_response(response)

        except Exception as e:
            self.logger.error("request_error", method=method, error=str(e))
            await self._send_error(req_id, -32603, "Internal error")

    async def _pump_messages(self, sub_id: int, method: str, params: list):
        """
        Pump messages from broker to WebSocket.

        Runs as a task for each subscription.
        """
        try:
            async for message in self.broker.subscribe(method, params):
                # Send notification
                await self._send_notification(method, sub_id, message)

                # Track message
                self.sub_manager.record_message(sub_id)

        except asyncio.CancelledError:
            # Normal cancellation when unsubscribing
            pass
        except Exception as e:
            self.logger.error(
                "pump_error", sub_id=sub_id, method=method, params=params, error=str(e)
            )

    @staticmethod
    async def _send_response(response):
        """Send JSON-RPC response.

        Build dict manually instead of using model_dump() because Pydantic
        converts dataclass-like objects (e.g. @structure Codable types) into
        dicts, which prevents json_default from encoding them as base64 blobs.
        """
        data = {"jsonrpc": "2.0", "id": response.id}
        if response.error is not None:
            data["error"] = response.error
        else:
            data["result"] = response.result
        await websocket.send(json.dumps(data, default=json_default))

    @staticmethod
    async def _send_result(req_id: any, result: any):
        """Send successful result."""
        data = {"jsonrpc": "2.0", "id": req_id, "result": result}
        await websocket.send(json.dumps(data, default=json_default))

    @staticmethod
    async def _send_error(req_id: any, code: int, message: str):
        """Send error response."""
        data = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
        await websocket.send(json.dumps(data, default=json_default))

    @staticmethod
    async def _send_notification(method: str, sub_id: int, result: any):
        """Send subscription notification (no id)."""
        data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": {"subscription": sub_id, "result": result},
        }
        await websocket.send(json.dumps(data, default=json_default))
