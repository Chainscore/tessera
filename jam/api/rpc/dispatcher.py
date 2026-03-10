"""
Dispatcher

Central request router.
Routes requests to handlers. Passes raw params, handlers parse themselves.
"""

import inspect
import structlog

from typing import Any, TYPE_CHECKING

from jam.api.rpc.types import RpcRequest, RpcResponse, RpcError

if TYPE_CHECKING:
    from jam.jam_node import JamNode
    from jam.api.rpc.handlers.chain import ChainHandler
    from jam.api.rpc.handlers.account import ServiceHandler
    from jam.api.rpc.handlers.work_package import WorkPackageHandler


class Dispatcher:
    """
    Central dispatcher for all RPC requests.

    Passes raw params to handlers, which parse themselves.
    """

    def __init__(
        self,
        jam: "JamNode",
        chain_handler: "ChainHandler",
        service_handler: "ServiceHandler",
        work_package_handler: "WorkPackageHandler",
    ):
        self.logger = structlog.get_logger("rpc")
        self.jam = jam

        self._chain = chain_handler
        self._service = service_handler
        self._work_package = work_package_handler

        # Methods
        self._methods = self._build_method_table()
        self._subscription_methods = self._build_sub_method_table()

    def _build_method_table(self) -> dict[str, tuple]:
        """Build method routing table."""
        return {
            # Chain methods
            "parameters": (self._chain, "parameters"),
            "bestBlock": (self._chain, "best_block"),
            "finalizedBlock": (self._chain, "finalized_block"),
            "parent": (self._chain, "parent"),
            "stateRoot": (self._chain, "state_root"),
            "beefyRoot": (self._chain, "beefy_root"),
            "statistics": (self._chain, "statistics"),
            "syncState": (self._chain, "sync_state"),
            "blockRequest": (self._chain, "block_request_handler"),

            # Service methods
            "serviceData": (self._service, "service_data"),
            "serviceValue": (self._service, "service_value"),
            "servicePreimage": (self._service, "service_preimage"),
            "serviceRequest": (self._service, "service_request"),
            "listServices": (self._service, "list_services"),
            "submitPreimage": (self._service, "submit_preimage"),

            # Work Package methods
            "workReport": (self._work_package, "work_report"),
            "submitWorkPackage": (self._work_package, "submit_work_package"),
            "submitWorkPackageBundle": (self._work_package, "submit_work_package_bundle"),
            "workPackageStatus": (self._work_package, "work_package_status"),
            "fetchWorkPackageSegments": (self._work_package, "fetch_work_package_segments"),
            "fetchSegments": (self._work_package, "fetch_segments"),
        }

    def _build_sub_method_table(self) -> dict[str, tuple]:
        """Build subscription method routing table."""
        return {
            # Chain methods
            "subscribeSyncStatus": (self._chain, "sync_status"),
            "subscribeBestBlock": (self._chain, "best_block"),
            "subscribeFinalizedBlock": (self._chain, "finalized_block"),
            "subscribeStatistics": (self._chain, "statistics"),

            # Service methods
            "subscribeServiceData": (self._service, "service_data"),
            "subscribeServiceValue": (self._service, "service_value"),
            "subscribeServicePreimage": (self._service, "service_preimage"),
            "subscribeServiceRequest": (self._service, "service_request"),

            # Work Package methods
            "subscribeWorkPackageStatus": (self._work_package, "work_package_status"),
        }


    async def dispatch(self, request: RpcRequest) -> RpcResponse:
        """
        Dispatch an RPC request to the appropriate handler.
        Passes raw params to handlers, which parse themselves.

        Args:
            request: The JSON-RPC request

        Returns:
            JSON-RPC response
        """
        method_name = request.method

        try:
            # Get handler and method
            handler, method = self._methods.get(method_name, (None, None))
            if not handler:
                raise RpcError(-32601, f"Method not found: {method_name}")

            # Call handler method with RAW params
            handler_method = getattr(handler, method)
            result = handler_method(request.params)

            # Handle async methods
            if inspect.isawaitable(result):
                result = await result

            self.logger.debug("Request dispatched!", method=method_name, id=request.id)
            return RpcResponse(id=request.id, result=result)

        except RpcError as e:
            self.logger.warning(
                "rpc_error", method=method_name, error_code=e.code, error_message=e.message
            )
            return RpcResponse(id=request.id, error=e.to_dict())
        except Exception as e:
            self.logger.error("internal_error", method=method_name, error=str(e), exc_info=True)
            return RpcResponse(
                id=request.id,
                error={"code": -32603, "message": "Internal error", "data": str(e)},
            )

    def get_initial_subscription_data(self, method: str, params: list) -> Any:
        """Get initial data for a subscription.

        Chain subscriptions pass a `finalized` boolean as their last param.
        When detected, the raw result is wrapped in a ChainSubUpdate envelope:
            {"header_hash": Hash, "slot": Number, "value": <raw_result>}
        """
        handler_info = self._subscription_methods.get(method)
        if not handler_info:
            return None

        handler, method_name = handler_info
        handler_method = getattr(handler, method_name)

        # Convert subscription params to method params
        method_params = self.sub_to_method(method, params)

        # Call method
        result = handler_method(method_params)

        # If last param is finality -> chain subscription
        if params and isinstance(params[-1], bool):
            block = self.jam.grandpa.load_final() if params[-1] else self.jam.grandpa.load_best()
            if block:
                return {
                    "header_hash": block.header.hash(),
                    "slot": block.header.slot,
                    "value": result,
                }

        return result

    def get_head(self, finalized: bool = True):
        grandpa = self.jam.grandpa

        # block can not be none here if grandpa is correctly implemented
        block = grandpa.load_final() if finalized else grandpa.load_best()
        return block.header.hash()

    def sub_to_method(self, method: str, params: list) -> list:
        """Convert subscription params to regular method params."""
        if not params:
            return []

        finalized = params[-1]
        header_hash = self.get_head(finalized)
        final_params = [header_hash, *params[:-1]]
        return final_params

    def is_subscription_method(self, method: str) -> bool:
        """Check if a method is a subscription method using manager."""
        return method in self._subscription_methods

    def is_unsubscribe_method(self, method: str) -> bool:
        """Check if a method is an unsubscribe method using manager."""
        return method.startswith("unsubscribe") and method[2:] in self._subscription_methods

