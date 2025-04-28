from dataclasses import dataclass
from jam.state.state import State
from jam.types import Int, Array
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.work.package import WorkPackage
from jam.utils.json import JsonSerde
from typing import cast, Any, Optional, Tuple
from jam.types.protocol.crypto import  WorkReportHash


@decodable_dataclass
@dataclass
class CE136Data(Codable, JsonSerde):
    work_report_hash: WorkReportHash


class WorkReportRequest(NetworkProtocol):
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE136

    def transmit(self, node: Node, data: CE136Data):

        for client in node.connections:
            message = self._prefix.encode() + data.work_report_hash.encode()
            client.stream_and_close(message=message)

    @classmethod
    def intercept(cls, buffer: bytes) -> CE136Data:
        data, offset = CE136Data.decode_from(buffer)
        data = cast(CE136Data, data)

        return data
        # return data.package_data, data.extrinsics

    @classmethod
    def process(cls, data: CE136Data):
        print("Processing work package")


    # @classmethod
    # def intercept_ext(cls, buffer: bytes) -> Tuple[WorkPackage, Array[WorkPackage]]:
    #     data, offset = CE136Data.decode_from(buffer)
    #
    #     data = cast(CE136Data, data)
    #
    #     return (data.package_data, data.extrinsics)

