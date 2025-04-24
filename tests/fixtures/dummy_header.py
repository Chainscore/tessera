from jam.types import (
    HeaderHash,
    StateRoot,
    OpaqueHash,
    TimeSlot,
    ValidatorIndex,
    BandersnatchVrfSignature,
    TicketBody,
    Entropy,
    BandersnatchPublic,
)
from jam.types.base.null import Null
from jam.types.extrinsics.tickets import TicketId, TicketAttempt
from jam.types.header import (
    Header,
    OptionalEpochMark,
    OptionalTicketsMark,
    OffendersMark,
    TicketsMark,
)
from jam.types.protocol.epoch import EpochMark
from jam.utils.constants import VALIDATOR_COUNT, EPOCH_LENGTH
from tests.fixtures.utils import create_dummy_bytes32, create_dummy_bytes


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
