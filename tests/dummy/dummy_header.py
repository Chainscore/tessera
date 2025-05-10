from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.crypto import (
    HeaderHash,
    StateRoot,
    OpaqueHash,
    BandersnatchVrfSignature,
)
from jam.types.base.null import Null
from jam.types.header import (
    Header,
    OptionalEpochMark,
    OptionalTicketsMark,
    OffendersMark,
)
from tests.dummy.utils import create_dummy_bytes32, create_dummy_bytes


def create_dummy_header() -> Header:
    """Create dummy header"""
    return Header(
        parent=HeaderHash(create_dummy_bytes32()),
        parent_state_root=StateRoot(create_dummy_bytes32()),
        extrinsic_hash=OpaqueHash(create_dummy_bytes32()),
        slot=TimeSlot(0),
        epoch_mark=OptionalEpochMark(Null),
        tickets_mark=OptionalTicketsMark(Null),
        offenders_mark=OffendersMark([]),
        entropy_source=BandersnatchVrfSignature(create_dummy_bytes(96)),
        author_index=ValidatorIndex(0),
        seal=BandersnatchVrfSignature(create_dummy_bytes(96)),
    )
