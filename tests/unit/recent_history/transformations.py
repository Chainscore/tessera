from jam.merklization import MMR
from jam.state.components.beta import Beta, BlockHistory
from jam.state.state import State
from jam.types import Boolean
from jam.types.protocol.crypto import StateRoot, HeaderHash
from jam.types.work import WorkReport
from jam.types.block import Block

from jam.recent_history.recent_history import RecentHistory

from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_extrinsics import create_dummy_work_report, create_dummy_validator_signatures
from tests.fixtures.dummy_state import create_dummy_state

from .types import Input, PreState, Testcase
from jam.types.extrinsics import GuaranteesExtrinsic, ReportGuarantee
from jam.types.work.report import SegmentRootLookup, SegmentRootLookupItem
from jam.types.protocol.core import TimeSlot


def create_work_report_from_input(input: Input) -> WorkReport:
    """Create work report lookup from test input"""
    work_report = create_dummy_work_report()
    lookup = SegmentRootLookup([])

    for item in input.work_packages:
        lookup_item = SegmentRootLookupItem(item.hash, item.exports_root)
        lookup.append(lookup_item)

    work_report.segment_root_lookup = lookup

    return work_report

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""

    block = create_dummy_block()
    block.header.parent = HeaderHash(input.header_hash)
    block.header.parent_state_root = StateRoot(input.parent_state_root)
    block.extrinsic.guarantees = GuaranteesExtrinsic(
        [
            ReportGuarantee(
                report=create_work_report_from_input(input),
                slot=TimeSlot(42),
                signatures=create_dummy_validator_signatures(),
            )
        ]
    )

    return block

def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""

    state: State = create_dummy_state()
    beta_dash = Beta([])

    for history in pre_state.beta:
        mmr = MMR(history.mmr.peaks)


        block = BlockHistory(history.header_hash, mmr, history.state_root, history.reported.to_dict())
        beta_dash.append(block)

    state.beta = beta_dash
    return state

def vector_transition(vector: Testcase) -> Boolean:
    """Test Function for Beta Transition"""
    test_block = create_block_from_input(vector.input)
    test_state = create_state_from_pre(vector.pre_state)

    state_dash = RecentHistory.transition(test_state, test_block, vector.input.accumulate_root)
    post_state_beta = vector.post_state.beta.to_beta()
    assert state_dash.beta == post_state_beta


    return Boolean(True)