from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from jam.network.base.quic import QuicProtocol
    from jam.network.node import Node

from tsrkit_types.enum import Uint

U8 = Uint[8]


class PrefixType:
    # UP Streams
    UP0 = U8(0)

    # CE Streams
    CE128 = U8(128)
    CE129 = U8(129)
    CE130 = U8(130)
    CE131 = U8(131)
    CE132 = U8(132)
    CE133 = U8(133)
    CE134 = U8(134)
    CE135 = U8(135)
    CE136 = U8(136)
    CE137 = U8(137)
    CE138 = U8(138)
    CE139 = U8(139)
    CE140 = U8(140)
    CE141 = U8(141)
    CE142 = U8(142)
    CE143 = U8(143)
    CE144 = U8(144)
    CE145 = U8(145)
    CE201 = U8(201)


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
