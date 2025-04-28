from dataclasses import dataclass
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

@decodable_dataclass
@dataclass
class CE133Data(Codable, JsonSerde):
    package_data: WorkPackageCore
    extrinsics: Int


class WorkPackageSubmission(NetworkProtocol):
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE133

    def transmit(self, node: Node, data: CE133Data):

        for client in node.connections:
            message = self._prefix.encode() + data.package_data.encode()
            stream_id = client.stream_and_keep_open(message=message)

            message = data.extrinsics.encode()
            client.stream_and_close(message=message, stream_id=stream_id)

    @classmethod
    def intercept(cls, buffer: bytes) -> CE133Data:
        data, offset = CE133Data.decode_from(buffer)
        data = cast(CE133Data, data)

        return data
        # return data.package_data, data.extrinsics

    @classmethod
    def process(cls, data: CE133Data):
        print("Processing work package")


    # @classmethod
    # def intercept_ext(cls, buffer: bytes) -> Tuple[WorkPackage, Array[WorkPackage]]:
    #     data, offset = CE133Data.decode_from(buffer)
    #
    #     data = cast(CE133Data, data)
    #
    #     return (data.package_data, data.extrinsics)