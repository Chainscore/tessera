from tsrkit_types import Null
from jam.block.header.tickets_mark import TicketsMark
from jam.block.header.epoch_mark import EpochMark

"""Common test utilities and data for disputes tests"""
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32, U8, Uint
from tsrkit_types.bool import Bool
from tsrkit_types.option import Option

from jam.block.block import Block
from jam.block.extrinsics.extrinsic import Extrinsic
from jam.block.extrinsics.disputes import (
    DisputesExtrinsic,
    Verdicts,
    Culprits,
    Faults,
    Verdict,
    Culprit,
    Fault,
    Judgement,
    JudgementVotes,
)
from jam.block.extrinsics.tickets import TicketsExtrinsic
from jam.block.extrinsics.preimages import PreimagesExtrinsic
from jam.block.extrinsics.guarantees import GuaranteesExtrinsic
from jam.block.extrinsics.assurances import AssurancesExtrinsic
from jam.block.header import Header, OffendersMark
from jam.settings import Settings
from jam.models.state.sigma import Sigma
from jam.models.state.psi import Psi, PsiG, PsiB, PsiW, PsiO
from jam.models.state.rho import Rho, OptionalWorkReportState
from jam.models.state.lambda_ import Lambda_
from jam.models.state.kappa import Kappa
from jam.models.protocol.crypto import (
    Ed25519Public,
    Ed25519Signature,
    WorkReportHash,
    BandersnatchPublic,
    BlsPublic,
)
from jam.models.protocol.core import ValidatorIndex, TimeSlot
from jam.models.protocol.validators import ValidatorData, ValidatorMetadata
from jam.models import BandersnatchVrfSignature
from jam.utils.constants import VALIDATOR_COUNT, X
from jam.utils.dummy.utils import create_dummy_bytes, create_dummy_bytes32


def deepcopy(obj):
    return obj.__class__.from_json(obj.to_json())


def create_dummy_validator_data() -> list[ValidatorData]:
    """Create dummy validator data for testing"""
    return [Settings(None, i).val for i in range(VALIDATOR_COUNT)]


def create_test_state(
    tau: U32 = U32(0),  # Default to epoch 0
    psi_good: list[WorkReportHash] = None,
    psi_bad: list[WorkReportHash] = None,
    psi_wonky: list[WorkReportHash] = None,
    psi_offenders: list[Ed25519Public] = None,
    rho_entries: list[OptionalWorkReportState] = None,
) -> Sigma:
    """Create a test state with specified dispute records"""
    from jam.utils.dummy.dummy_state import create_dummy_state

    # Start with a complete dummy state
    state = create_dummy_state()

    # Override tau
    state.tau = tau

    # Override psi with test data
    state.psi = Psi(
        good=PsiG(psi_good or []),
        bad=PsiB(psi_bad or []),
        wonky=PsiW(psi_wonky or []),
        offenders=PsiO(psi_offenders or []),
    )

    # Override rho if provided
    if rho_entries:
        state.rho = Rho(rho_entries)

    return state


def create_test_block(disputes_extrinsic: DisputesExtrinsic = None) -> Block:
    """Create a test block with specified disputes extrinsic"""
    if disputes_extrinsic is None:
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([]), culprits=Culprits([]), faults=Faults([])
        )

    extrinsic = Extrinsic(
        tickets=TicketsExtrinsic([]),
        preimages=PreimagesExtrinsic([]),
        guarantees=GuaranteesExtrinsic([]),
        assurances=AssurancesExtrinsic([]),
        disputes=disputes_extrinsic,
    )

    return Block(
        header=Header(
            parent=Bytes[32](create_dummy_bytes32()),
            parent_state_root=Bytes[32](create_dummy_bytes32()),
            extrinsic_hash=Bytes[32](create_dummy_bytes32()),
            slot=TimeSlot(100),
            epoch_mark=EpochMark(Null),
            tickets_mark=TicketsMark(Null),
            offenders_mark=OffendersMark([]),
            author_index=ValidatorIndex(0),
            entropy_source=BandersnatchVrfSignature(create_dummy_bytes(784)),
            seal=BandersnatchVrfSignature(create_dummy_bytes(784)),
        ),
        extrinsic=extrinsic,
    )


def create_valid_judgement_votes(
    target_hash: bytes, vote_value: bool, count: int
) -> JudgementVotes:
    """Create valid judgement votes for testing"""
    votes = []
    for i in range(count):
        keys = Settings(None, i)
        votes.append(
            Judgement(
                vote=Bool(vote_value),
                index=ValidatorIndex(i),
                signature=Ed25519Signature(
                    Ed25519PrivateKey.from_private_bytes(keys.ed25519_private).sign(
                        (X.VALID if vote_value else X.INVALID).value + target_hash
                    )
                ),
            )
        )
    return JudgementVotes(votes)


def create_sorted_culprits(target: WorkReportHash, keys: list[int]) -> list[Culprit]:
    """Create culprits sorted by key"""
    sorted_keys = sorted(keys)
    culprits = []
    for key in sorted_keys:
        keys = Settings(None, key)
        culprits.append(
            Culprit(
                target=target,
                key=Bytes[32](keys.ed25519_public),
                signature=Ed25519Signature(
                    Ed25519PrivateKey.from_private_bytes(keys.ed25519_private).sign(
                        X.GUARANTEE.value + target
                    )
                ),
            )
        )
    return culprits


def create_sorted_faults(
    target: WorkReportHash, vote: bool, keys: list[Ed25519Public]
) -> list[Fault]:
    """Create faults sorted by key"""
    sorted_faults = sorted(keys)
    faults = []
    for key in sorted_faults:
        keys = Settings(None, key)
        faults.append(
            Fault(
                target=target,
                vote=Bool(vote),
                key=Bytes[32](keys.ed25519_public),
                signature=Ed25519Signature(
                    Ed25519PrivateKey.from_private_bytes(keys.ed25519_private).sign(
                        (X.VALID if vote else X.INVALID).value + target
                    )
                ),
            )
        )
    return faults


def create_sorted_verdicts(
    verdicts_data: list[tuple[WorkReportHash, U32, bool, int]],
) -> list[Verdict]:
    """Create verdicts sorted by target hash

    Args:
        verdicts_data: List of (target_hash, age, vote_value, vote_count) tuples
    """
    verdicts = []
    for target, age, vote_value, vote_count in verdicts_data:
        verdict = Verdict(
            target=target,
            age=age,
            votes=create_valid_judgement_votes(target, vote_value, vote_count),
        )
        verdicts.append(verdict)

    # Sort by target hash
    verdicts.sort(key=lambda v: v.target)
    return verdicts


def get_state_counts(state: Sigma) -> dict:
    """Get counts of all dispute sets"""
    return {
        "good": len(state.psi.good),
        "bad": len(state.psi.bad),
        "wonky": len(state.psi.wonky),
        "offenders": len(state.psi.offenders),
    }


def assert_state_counts(
    initial_counts: dict,
    new_state: Sigma,
    good_delta: int = 0,
    bad_delta: int = 0,
    wonky_delta: int = 0,
    offenders_delta: int = 0,
):
    """Assert that state counts changed by expected deltas"""
    assert len(new_state.psi.good) == initial_counts["good"] + good_delta
    assert len(new_state.psi.bad) == initial_counts["bad"] + bad_delta
    assert len(new_state.psi.wonky) == initial_counts["wonky"] + wonky_delta
    assert len(new_state.psi.offenders) == initial_counts["offenders"] + offenders_delta


def assert_targets_in_sets(
    new_state: Sigma,
    good_targets: list[WorkReportHash] = None,
    bad_targets: list[WorkReportHash] = None,
    wonky_targets: list[WorkReportHash] = None,
    offender_keys: list[Ed25519Public] = None,
):
    """Assert that specific targets/keys are in the respective sets"""
    if good_targets:
        for target in good_targets:
            assert target in new_state.psi.good

    if bad_targets:
        for target in bad_targets:
            assert target in new_state.psi.bad

    if wonky_targets:
        for target in wonky_targets:
            assert target in new_state.psi.wonky

    if offender_keys:
        for key in offender_keys:
            k = Settings(None, key)
            assert k.ed25519_public in new_state.psi.offenders
