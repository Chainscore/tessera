from typing import List

from jam.authorization.authorization import Authorization
from jam.merklization.mountain_merkle import OptionHash
from jam.recentHistory.recentHistory import RecentHistory
from jam.state.state import State
from jam.types import Boolean, TimeSlot, WorkReport, SegmentRootLookupItem, Vector, String, ByteArray32, OpaqueHash
from jam.types.base.sequences import vector
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic, ReportGuarantee
from jam.types.work.report import SegmentRootLookup
from tests.fixtures.dummy_extrinsics import (
    create_dummy_work_report,
    create_dummy_validator_signatures,
)
from tests.unit.recent_history.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with, PackageDictInput, BetaInput, MMRInput,
)
from tests.fixtures.dummy_state import create_dummy_state
from tests.fixtures.dummy_block import create_dummy_block
from jam.state.components.beta import PackageDict, Beta, BlockHistory
from jam.merklization import MMR
from jam.types.protocol.core import SegmentRoot, WorkPackageHash


def create_work_report_from_input(input: Input) -> WorkReport:
    workReport = create_dummy_work_report()
    lookup = SegmentRootLookup()

    for item in input.work_packages:
        lookup_item = SegmentRootLookupItem(item.hash, item.exports_root)
        # lookup_item.work_package_hash = item.hash
        # lookup_item.segment_tree_root = item.exports_root
        lookup.append(lookup_item)

    workReport.segment_root_lookup = lookup

    return workReport

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.guarantees = GuaranteesExtrinsic(
        [
            ReportGuarantee(
                report=create_work_report_from_input(input),
                slot=TimeSlot(42),
                signatures=create_dummy_validator_signatures(),
            )
            # for _ in input.auths
        ]
    )

    # for i, auth in enumerate(input.auths):
    #     block.extrinsic.guarantees[i].report.core_index = auth.core
    #     block.extrinsic.guarantees[i].report.authorizer_hash = auth.auth_hash

    return block

def convertMMR(mmr_input: MMRInput) -> MMR:
    # print("final dagger dash", mmr_input)
    # print("final dagger dash dash", mmr_input['peaks'])
    # return mmr_input['peaks']

    hashes = []
    for root in mmr_input['peaks']:
        # print('root value',root)
        if root:
            hashed = OptionHash(ByteArray32(root))
            # hashed = OpaqueHash(root)
            hashes.append(hashed)
    # print("dagger baba", MMR(hashes))
    return MMR(hashes)


def convertWorkPackages(packages_input: PackageDictInput) -> PackageDict:
    package_dict: PackageDict[WorkPackageHash, SegmentRoot] = PackageDict()
    for package in packages_input:
        hash: WorkPackageHash = package.hash
        export_root: SegmentRoot = package.exports_root
        package_dict[hash] = export_root

    return package_dict

def convertBeta(beta_input: BetaInput) -> Beta:
    new_beta = Beta([])
    for history in beta_input:
        block_history = BlockHistory(history.value, convertMMR(history.mmr), history.state_root, convertWorkPackages(history.reported))
        new_beta.append(block_history)

    return new_beta

# def create_prestate_from_input(pre_state: PreState, input: Input)

def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    state.beta = convertBeta(pre_state.beta)
    return state


def vector_transition(vector: Testcase) -> Boolean:
    test_block = create_block_from_input(vector.input)
    test_state = create_state_from_pre(vector.pre_state)
    # print("beta before block", test_state.beta)
    # print("Beta after block", test_state.beta)
    try:
        # print("comp",type(test_block), Block)
        # hist = ()

        # print('test_state.beta', str(test_state.beta))
        output = RecentHistory.transition(pre_state=test_state, block=test_block, header_hash=vector.input.header_hash, accumulate_root=vector.input.accumulate_root)
        # print('oooooo',output.beta)
        # print('pppppp',vector.post_state.beta)

        # postop = convertBeta(vector.post_state.beta)
        # print("final dagger", postop)
        print(output.beta)
        assert output.beta
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)


def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=4)
    # a=get_testcases_starting_with(limit=4)
    print(type(vectors))
    # print(type(a))
    for i, vector in enumerate(vectors):
        # print(type(vector))
        # print(type(i))
        # print(vector.input.work_packages)

        # print("vectror", vector)
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")
