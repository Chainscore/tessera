"""
JIP-2 compliant JSON-RPC 2.0 service for JAM nodes.

RPCService → Dispatcher → Handlers (chain, service, work_package)
           → Broker (pub/sub) + SubscriptionManager (lifecycle)
           → Routes (HTTP, WebSocket)
"""

from jam.api.rpc.service import RPCService

__all__ = ["RPCService"]
