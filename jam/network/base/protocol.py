from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from jam.network.base.quic import QuicProtocol
    from jam.network.node import Node

from tsrkit_types.enum import Enum

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
    CE144 = 144
    CE145 = 145
    CE201 = 201


class NetworkProtocol(ABC):
    """
    Base Network Protocol

    Flow:
        - Node initiates connection.
        - Uses transmit function to send query / data.
        - Uses server intercept to process received query / data.
        - Returns acknowledgement / data on same stream id.
        - Uses client intercept to process received ack / data.
    """

    _prefix: PrefixType
    max_buffer_size: int

    @abstractmethod
    async def transmit(self, node: "Node", data: Any):
        """
        Function to transmit data to connected node.
        Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def req_intercept(self, stream_id: int, server: "QuicProtocol"):
        """
        Function to intercept & process data / query from connected node.
        And sends acknowledgement / response to the node.
        Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    def res_intercept(self, stream_id: int, client: "QuicProtocol"):
        """
        Function to intercept & process returned data from connected node.
        Must be implemented by subclasses.
        """
        ...