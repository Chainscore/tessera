from abc import ABC, abstractmethod
from typing import Any

from jam.state.state import State
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
    from jam.network.node import Node

    is_active: bool
    _prefix: PrefixType
    max_buffer_size: int

    async def activate(self):
        ...

    async def deactivate(self):
        ...

    @abstractmethod
    def transmit(self, node: Node, data: Any):
        """
        Function to transmit data to connected server.
        Called on client. Must be implemented by subclasses.
        """
        ...

    @classmethod
    @abstractmethod
    def server_intercept(cls, buffer: bytes):
        """
        Function to intercept & process data / query from connected client.
        Called on server. Must be implemented by subclasses.
        """
        ...


    @classmethod
    @abstractmethod
    def client_intercept(cls, buffer: bytes):
        """
        Function to intercept & process returned data from connected server.
        Called on client. Must be implemented by subclasses.
        """
        ...