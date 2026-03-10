"""
HTTP Route

HTTP JSON-RPC endpoint handler.
"""

import json
from quart import Quart, request, Response
from typing import TYPE_CHECKING
import structlog

from jam.api.rpc.types import RpcRequest, RpcResponse
from jam.api.rpc.utils.serialization import json_default

if TYPE_CHECKING:
    from jam.api.rpc.dispatcher import Dispatcher


class HTTPRoute:
    """
    HTTP JSON-RPC endpoint.

    Thin adapter that:
    1. Parses JSON body
    2. Calls dispatcher
    3. Returns JSON response
    """

    def __init__(self, app: Quart, dispatcher: "Dispatcher"):
        self.app = app
        self.dispatcher = dispatcher
        self.logger = structlog.get_logger("rpc")
        self._register()

    def _register(self):
        """Register HTTP route with Quart."""

        @self.app.route("/", methods=["POST"])
        async def rpc_handler():
            """Handle HTTP JSON-RPC requests."""
            try:
                # Parse JSON body
                data = await request.get_json()

                if not data:
                    error_json = json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "error": {"code": -32700, "message": "Parse error"},
                            "id": None,
                        }
                    )
                    return Response(error_json, mimetype="application/json"), 400

                # Create request object
                req = RpcRequest(**data)

                self.logger.debug("http_request", method=req.method, id=req.id)

                # Dispatch to handler
                response = await self.dispatcher.dispatch(req)

                # Build response dict
                data = {"jsonrpc": "2.0", "id": response.id}
                if response.error is not None:
                    data["error"] = response.error
                else:
                    data["result"] = response.result
                json_str = json.dumps(data, default=json_default)

                # Return JSON response
                return Response(json_str, mimetype="application/json"), 200

            except json.JSONDecodeError:
                self.logger.warning("json_parse_error")
                error_json = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error"},
                        "id": None,
                    }
                )
                return Response(error_json, mimetype="application/json"), 400
            except Exception as e:
                self.logger.error("http_error", error=str(e), exc_info=True)
                error_json = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": "Internal error"},
                        "id": None,
                    }
                )
                return Response(error_json, mimetype="application/json"), 500
