"""
Telemetry module for jamtart integration.

Provides JIP-3 compliant telemetry for JAM node operations.
Events are sent to a jamtart backend via binary TCP protocol.
"""
from .client import TelemetryClient, TelemetryConfig, get_client, emit_event

__all__ = [
    "TelemetryClient",
    "TelemetryConfig",
    "get_client",
    "emit_event",
]
