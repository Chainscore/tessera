from abc import ABC, abstractmethod
from typing import Any

from jam.network.quic.server import QuicServerProtocol
from jam.types.base.enum import Enum

class PrefixType(Enum):
    # UP Streams
    UP0 = 0

    # CE Streams
    CE128 = 128
    CE129 = 129
    CE130 = 130
    CE131 = 131
    CE132 = 132
    CE133 = 133
    CE134 = 134
    CE135 = 135
    CE136 = 136
    CE137 = 137
    CE138 = 138
    CE139 = 139
    CE140 = 140
    CE141 = 141
    CE142 = 142
    CE143 = 143


class NetworkProtocol(ABC):
    """
    Base Network Protocol

    Flow:
        - QUIC Client initiates connection.
        - Uses transmit function to send data.
        - QUIC Server intercepts and processes received data.
        - Uses send_acknowledgment function to return ack / data on same stream id.
        - QUIC Client then intercepts response and processes it.
    """

    from jam.network.node import Node

    _prefix: PrefixType
    max_buffer_size: int

    @abstractmethod
    def transmit(self, node: Node, data: Any):
        """
        Function to transmit data to connected server.
        Called on client. Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """
        Function to intercept & process data / query from connected client.
        And sends acknowledge / response to the client
        Called on server. Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def client_intercept(self, buffer: bytes, stream_id: int):
        """
        Function to intercept & process returned data from connected server.
        Called on client. Must be implemented by subclasses.
        """
        ...