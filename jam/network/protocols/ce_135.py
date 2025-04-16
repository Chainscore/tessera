from dataclasses import dataclass
from jam.state.state import State
from jam.types import Int, Array
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.work.package import WorkPackage
from jam.utils.json import JsonSerde
from typing import cast, Any, Optional, Tuple
from jam.types.work.report import WorkReport
from jam.types.protocol.core import TimeSlot


@decodable_dataclass
@dataclass
class CE135Data(Codable, JsonSerde):
    report: WorkReport
    slot: TimeSlot


class WorkReportDistribution(NetworkProtocol):
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE135

    def transmit(self, node: Node, data: CE135Data):

        for client in node.connections:
            message = self._prefix.encode() + data.report.encode() + data.slot.encode()
            client.stream_and_close(message=message)

    @classmethod
    def intercept(cls, buffer: bytes) -> CE135Data:
        data, offset = CE135Data.decode_from(buffer)
        data = cast(CE135Data, data)

        return data
        # return data.package_data, data.extrinsics

    @classmethod
    def process(cls, data: CE135Data):
        print("Processing work package")


    # @classmethod
    # def intercept_ext(cls, buffer: bytes) -> Tuple[WorkPackage, Array[WorkPackage]]:
    #     data, offset = CE135Data.decode_from(buffer)
    #
    #     data = cast(CE135Data, data)
    #
    #     return (data.package_data, data.extrinsics)

