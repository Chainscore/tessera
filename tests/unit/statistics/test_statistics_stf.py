from typing import List

from jam.state.components.pi import AllValidatorStats, Pi
from jam.state.state import State
from jam.statistics.statistics import Statistics
from jam.types import BandersnatchRingVrfSignature, Boolean, Ed25519Signature, TimeSlot
from jam.types.block import Block
from jam.types.extrinsics.assurances import AssurancesExtrinsic, AvailAssurance
from jam.types.extrinsics.guarantees import (
    GuaranteesExtrinsic,
    ReportGuarantee,
    ValidatorSignature,
)
from jam.types.extrinsics.preimages import Preimage, PreimagesExtrinsic
from jam.types.extrinsics.tickets import TicketEnvelope, TicketsExtrinsic
from jam.types.protocol.core import ServiceId, ValidatorIndex
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_extrinsics import (
    create_dummy_work_report,
)
from tests.fixtures.dummy_state import create_dummy_state
from tests.fixtures.utils import create_dummy_bytes, create_dummy_bytes32
from tests.unit.statistics.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with,
)


def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.header.slot = input.slot
    block.header.author_index = input.author_index

    block.extrinsic.tickets = TicketsExtrinsic(
        [
            TicketEnvelope(
                attempt=ticket.attempt,
                signature=BandersnatchRingVrfSignature(create_dummy_bytes(784)),
            )
            for ticket in input.extrinsic.tickets
        ]
    )

    block.extrinsic.preimages = PreimagesExtrinsic(
        [
            Preimage(requester=ServiceId(0), blob=create_dummy_bytes32())
            for _ in input.extrinsic.preimages
        ]
    )

    block.extrinsic.guarantees = GuaranteesExtrinsic(
        [
            ReportGuarantee(
                report=create_dummy_work_report(),
                slot=TimeSlot(42),
                signatures=[
                    ValidatorSignature(
                        validator_index=ValidatorIndex(signature.validator_index),
                        signature=Ed25519Signature(create_dummy_bytes(64)),
                    )
                    for signature in guarantee.signatures
                ],
            )
            for guarantee in input.extrinsic.guarantees
        ]
    )

    block.extrinsic.assurances = AssurancesExtrinsic(
        [
            AvailAssurance(
                anchor=create_dummy_bytes32(),
                bitfield="0x01",
                validator_index=ValidatorIndex(assurance.validator_index),
                signature=Ed25519Signature(create_dummy_bytes(64)),
            )
            for assurance in input.extrinsic.assurances
        ]
    )

    return block


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    print("MURPH:", type(pre_state.pi.current), pre_state.pi.current)
    state.pi = Pi(
        [AllValidatorStats(pre_state.pi.current), AllValidatorStats(pre_state.pi.last)]
    )
    state.tau = pre_state.tau
    return state


def vector_transition(vector: Testcase) -> Boolean:
    test_block = create_block_from_input(vector.input)
    test_state = create_state_from_pre(vector.pre_state)
    try:
        output = Statistics.transition(test_state, test_block)
        assert output.pi[0] == vector.post_state.pi.current
        assert output.pi[1] == vector.post_state.pi.last
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)


def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=3)
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")
