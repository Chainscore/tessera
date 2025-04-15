from dataclasses import dataclass
from jam.network.node import Node
from jam.types import Int
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.work.package import WorkPackage
from jam.utils.json import JsonSerde
from typing import cast


@decodable_dataclass
@dataclass
class WorkPackageCore(Codable, JsonSerde):
    work_package : WorkPackage
    core_index : Int



class WorkPackageSubmission(NetworkProtocol):
    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE133

    async def transmit(self, node: Node, data:WorkPackageCore):

        for client in node.connections:
            await client.send_message(self._prefix.encode() + data.encode())

    @classmethod
    def intercept(cls, buffer: bytes) -> WorkPackageCore:
        data, offset = WorkPackageCore.decode_from(buffer)
        data = cast(WorkPackageCore, data)

        return data

