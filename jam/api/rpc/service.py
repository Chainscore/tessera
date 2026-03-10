"""
RPC Service

Main orchestrator for the RPC system.
Owned by JamNode and provides RPC functionality.
"""

from typing import TYPE_CHECKING
from quart import Quart
import structlog

from jam.api.rpc.broker import Broker
from jam.api.rpc.dispatcher import Dispatcher
from jam.api.rpc.subscriptions.manager import SubscriptionManager
from jam.api.rpc.handlers.chain import ChainHandler
from jam.api.rpc.handlers.account import ServiceHandler
from jam.api.rpc.handlers.work_package import WorkPackageHandler
from jam.api.rpc.handlers.subscriptions import SubscriptionPublisher
from jam.api.rpc.routes.http import HTTPRoute
from jam.api.rpc.routes.websocket import WebSocketRoute
from jam.api.rpc.utils.serialization import set_serialize_mode

if TYPE_CHECKING:
    from jam.jam_node import JamNode


class RPCService:
    """
    Main RPC Service orchestrator. Owned by JamNode.

    RPCService
      ├─ Dispatcher ─▶ ChainHandler, ServiceHandler, WorkPackageHandler
      ├─ Broker (pub/sub)
      ├─ SubscriptionManager (lifecycle + tracking)
      ├─ SubscriptionPublisher (event → broker bridge)
      └─ Routes: HTTPRoute, WebSocketRoute
    """

    def __init__(self, jam_node: "JamNode"):
        """
        Initialize RPC Service.

        Args:
            jam_node: Reference to JamNode for accessing state, settings, etc.
        """
        self._jam = jam_node
        self.logger = structlog.get_logger("rpc")

        # Set serialization mode based on RPC port
        # Port 19801 uses list(val) format; all others use base64
        rpc_port = int(jam_node.config.RPC_PORT)
        set_serialize_mode("list" if rpc_port == 19801 else "b64")

        # Create Quart app
        self._app = Quart(__name__)

        self.logger.debug("Initializing RPC!")

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize all RPC components."""

        # 1. Create handlers (main logic)
        self._chain_handler = ChainHandler(self._jam)
        self._service_handler = ServiceHandler(self._jam)
        self._work_package_handler = WorkPackageHandler(self._jam)

        # 2. Create broker (pub/sub)
        self._broker = Broker()

        # 3. Create dispatcher (routing)
        self._dispatcher = Dispatcher(
            self._jam, self._chain_handler, self._service_handler, self._work_package_handler
        )

        self._sub_manager = SubscriptionManager()

        # 5. Create subscription publisher (triggers)
        self._sub_publisher = SubscriptionPublisher(self._jam, self._broker)

        # 6. Create routes (rpc endpoints)
        self._http_route = HTTPRoute(self._app, self._dispatcher)
        self._ws_route = WebSocketRoute(
            self._app, self._dispatcher, self._broker, self._sub_manager
        )

    @property
    def app(self) -> Quart:
        """Access to Quart application."""
        return self._app

    @property
    def broker(self) -> Broker:
        """Access to message broker."""
        return self._broker

    @property
    def publisher(self) -> SubscriptionPublisher:
        """Access to subscription publisher."""
        return self._sub_publisher

    @property
    def active_subscriptions(self):
        return self._sub_manager


    async def start(self):
        """
        Start the RPC service.

        This runs the Quart HTTP/WebSocket server.
        Should be called from JamNode's main task group.
        """
        host = self._jam.config.RPC_HOST
        port = int(self._jam.config.RPC_PORT)

        self.logger.info("RPC Server starting", host=host, port=port)

        await self._app.run_task(
            debug=True, host=host, port=port, shutdown_trigger=self._jam.rpc_shutdown_trigger
        )

        self.logger.info("RPC Server stopped!")
