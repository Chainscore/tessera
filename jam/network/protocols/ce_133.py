from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.types.base.integers import Int

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass

from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.work.package import WorkPackage


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
    """
    CE 133 Protocol for submitting Work Package

    Protocol Flow:
        Builder -> Guarantor

        --> Core Index ++ Work-Package
        --> [Extrinsic]
        --> FIN
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-133-work-package-submission
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE133

    def transmit(self, node: Node, data: CE133Data):
        """Transmit Work Package from Builder (client) to Guarantor (server)"""

        stream_a = self._prefix.encode() + data.package_data.encode()
        stream_b = data.extrinsics.encode()

        logger.info(f"Transmitting Work-Package to {len(node.connections)} Validators")

        for client in node.connections:
            stream_id = client.stream_and_keep_open(message=stream_a)
            client.stream_and_close(message=stream_b, stream_id=stream_id)

    @classmethod
    def server_intercept(cls, buffer: bytes) -> CE133Data:
        """Intercept & Process Work Package on Guarantor (server)"""

        logger.info("Received Work Package")
        data, offset = CE133Data.decode_from(buffer)
        data = cast(CE133Data, data)

        logger.info("Processing Work Package")
        # TODO: Process received Work Package
        # process goes here

        return data

    @classmethod
    def client_intercept(cls, buffer: bytes):
        """Acknowledgement"""
        logger.info("Work Package received on Guarantor Node")


