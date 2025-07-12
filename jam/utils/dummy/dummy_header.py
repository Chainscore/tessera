from tsrkit_types import Option

from jam.block.header import TicketsMark, EpochMark
from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.crypto import (
    HeaderHash,
    StateRoot,
    OpaqueHash,
    BandersnatchVrfSignature,
)
from tsrkit_types import Null
from jam.block.header import (
    Header,
    OffendersMark,
)
from jam.utils.dummy.utils import create_dummy_bytes32, create_dummy_bytes


def create_dummy_header() -> Header:
    """Create dummy header"""
    return Header(
        parent=HeaderHash(create_dummy_bytes32()),
        parent_state_root=StateRoot(create_dummy_bytes32()),
        extrinsic_hash=OpaqueHash(create_dummy_bytes32()),
        slot=TimeSlot(0),
        epoch_mark=EpochMark(Null),
        tickets_mark=TicketsMark(Null),
        offenders_mark=OffendersMark([]),
        entropy_source=BandersnatchVrfSignature(create_dummy_bytes(96)),
        author_index=ValidatorIndex(0),
        seal=BandersnatchVrfSignature(create_dummy_bytes(96)),
    )
