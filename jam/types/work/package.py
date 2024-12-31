"""Work package types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence

from jam.types.base.bytes import Bytes
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ServiceId
from jam.types.work.item import WorkItem
from jam.types.work.refine_context import RefineContext
from jam.utils.constants import MAX_WORK_ITEMS

@dataclass
class Authorizer(Codable):
    """Authorizer structure."""
    code_hash: OpaqueHash
    params: Bytes

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.code_hash, self.params]

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        code_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        params = Bytes(buffer[current_offset:])
        return Authorizer(code_hash, params), len(buffer) - offset

@dataclass
class WorkPackage(Codable):
    """Work package structure."""
    authorization: Bytes
    auth_code_host: ServiceId
    authorizer: Authorizer
    context: RefineContext
    items: List[WorkItem]  # Size 1..4

    def __init__(self, authorization: Bytes, auth_code_host: ServiceId,
                 authorizer: Authorizer, context: RefineContext,
                 items: List[WorkItem]):
        if not (1 <= len(items) <= MAX_WORK_ITEMS):
            raise ValueError(f"Number of work items must be between 1 and {MAX_WORK_ITEMS}")
        self.authorization = authorization
        self.auth_code_host = auth_code_host
        self.authorizer = authorizer
        self.context = context
        self.items = items

    def enc_sequence(self) -> Sequence[Codable]:
        sequence: List[Codable] = [
            self.authorization,
            self.auth_code_host,
            self.authorizer,
            self.context
        ]
        sequence.extend(self.items)
        return sequence

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        authorization = Bytes(buffer[current_offset:])
        current_offset += len(authorization)
        auth_code_host, size = ServiceId.decode_from(buffer, current_offset)
        current_offset += size
        authorizer, size = Authorizer.decode_from(buffer, current_offset)
        current_offset += size
        context, size = RefineContext.decode_from(buffer, current_offset)
        current_offset += size

        items = []
        while current_offset < len(buffer) and len(items) < MAX_WORK_ITEMS:
            item, size = WorkItem.decode_from(buffer, current_offset)
            items.append(item)
            current_offset += size

        if not items:
            raise ValueError("Work package must contain at least one work item")

        return WorkPackage(
            authorization,
            auth_code_host,
            authorizer,
            context,
            items
        ), current_offset - offset
