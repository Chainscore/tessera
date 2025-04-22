from typing import Any

import distlib
from annotated_types.test_cases import cases
from httpx import stream
from isort.parse import CommentsAboveDict
from pydantic.v1.schema import json_scheme

from jam.types.base import Vector, ByteArray32, decodable_vector, Int
from jam.types.base.sequences import vector
from jam.utils.codec import Codable
from dataclasses import dataclass

from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.utils.json import JsonSerde
from jam.types.work.package import WorkPackage
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.crypto import Ed25519Signature
from jam.types.protocol.crypto import WorkReportHash
from jam.work_package.work_package import SegmentRootLookupDict
from tests.fixtures.dummy_package import create_dummy_package
from typing import cast, Any, Optional, Tuple
from tests.fixtures.dummy_package import crete_dummy_coreSegment, create_dummy_bundle



@decodable_dataclass
@dataclass
class CoreSegment(Codable, JsonSerde):
    core_index : Int
    length : Int
    segment_root_map : SegmentRootLookupDict


@decodable_vector
class Segments(Vector[ByteArray32]):
    ...

@decodable_dataclass
@dataclass
class WorkPackageBundle(Codable, JsonSerde):
    workPackage: WorkPackage
    extrinsic : OpaqueHash
    import_segment : Segments


@decodable_dataclass
@dataclass
class Credential(Codable, JsonSerde):
    workreportHash : WorkReportHash
    ed25519signature : Ed25519Signature


@decodable_dataclass
@dataclass
class CE134Data(Codable, JsonSerde):
    core_segment: CoreSegment
    work_package_bundle : WorkPackageBundle


class WorkPackageSharing(NetworkProtocol):
    from jam.network.node import Node

    def __init__(self):
        def __init__(self):
            super().__init__()
            self._prefix = PrefixType.CE134

    def transmit(self, node: Node, data: CE134Data):
        data = CE134Data(core_segment=crete_dummy_coreSegment(), work_package_bundle= create_dummy_bundle()  )
        for client in node.connections:
            message = self._prefix.encode() + data.core_segment.encode()
            stream_id = client.stream_and_keep_open(message=message)

            message = data.work_package_bundle.encode()
            client.stream_and_close(message=message, stream_id=stream_id)

    @classmethod
    def intercept(cls, buffer: bytes) -> CE134Data:
        data, offset = CE134Data.decode_from(buffer)
        data = cast(CE134Data, data)

        return data

    @classmethod
    def process(cls, data: CE134Data):
        ...