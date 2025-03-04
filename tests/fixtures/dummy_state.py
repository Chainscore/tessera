import pytest
from typing import Dict

from jam.state.components.alpha import Alpha, AuthorizationPool, AuthorizerHash
from jam.state.components.beta import Beta, BlockHistory, PackageDict
from jam.state.components.chi import Chi, ChiG
from jam.state.components.eta import Eta
from jam.consensus.safrole.gamma import Gamma, GammaK, GammaA, GammaS, GammaSTickets
from jam.state.components.delta import (
    Delta,
    AccountData,
    AccountStorage,
    PreImageLookup,
    LookupTimestamps,
    Timestamps,
    ServiceCodeHash,
)
from jam.state.components.iota import Iota
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_
from jam.state.components.pi import AllValidatorStats, Pi, ValidatorStat
from jam.state.components.psi import Psi, PsiB, PsiG, PsiO, PsiW
from jam.state.components.rho import OptionalWorkReportState, Rho
from jam.state.components.phi import AuthorizationQueue, Phi
from jam.state.components.tau import Tau
from jam.state.components.theta import AllReadyWRs, Theta
from jam.state.components.xi import Xi
from jam.types import TicketBody

from jam.types.base import Bytes
from jam.types.base.integers.fixed import U32
from jam.types.base.integers.general import Int
from jam.types.base.null import Nullable
from jam.types.protocol.crypto import (
    BlsPublic,
    Ed25519Public,
    HeaderHash,
    StateRoot,
    OpaqueHash,
    BandersnatchPublic,
    BandersnatchRingRoot,
)
from jam.types.protocol.core import (
    SegmentRoot,
    WorkPackageHash,
    Balance,
    Gas,
    ServiceId,
    WorkReportHash,
)
from jam.merklization import MMR
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from jam.utils.constants import (
    CORE_COUNT,
    MAX_AUTH_POOL_ITEMS,
    MAX_AUTH_QUEUE_ITEMS,
    VALIDATOR_COUNT,
    EPOCH_LENGTH,
)
from tests.fixtures.utils import create_dummy_bytes32, create_dummy_bytes
from jam.state.state import State


def create_dummy_state_components() -> Dict[str, object]:
    """Create dummy instances of all state components with realistic test data"""
    components = {}

    # Alpha - Array of authorization pools
    auth_pool = AuthorizationPool(
        [AuthorizerHash(create_dummy_bytes32()) for _ in range(MAX_AUTH_POOL_ITEMS)]
    )
    components["alpha"] = Alpha([auth_pool for _ in range(CORE_COUNT)])

    # Beta - Vector of block history
    package_dict = PackageDict(
        {
            WorkPackageHash(create_dummy_bytes32()): SegmentRoot(create_dummy_bytes32())
            for _ in range(3)  # Few dummy packages
        }
    )
    block = BlockHistory(
        header_hash=HeaderHash(create_dummy_bytes32()),
        mmr=MMR([]),
        state_root=StateRoot(create_dummy_bytes32()),
        packages=package_dict,
    )
    components["beta"] = Beta([block for _ in range(3)])

    # Create dummy validator data
    dummy_validator_data = [
        ValidatorData(
            bandersnatch=BandersnatchPublic(create_dummy_bytes32()),
            ed25519=Ed25519Public(create_dummy_bytes32()),
            bls=BlsPublic(create_dummy_bytes(144)),
            metadata=ValidatorMetadata(create_dummy_bytes(128)),
        )
        for _ in range(VALIDATOR_COUNT)
    ]

    # Gamma - Validator set
    validator_set = GammaK(dummy_validator_data)
    ring_root = BandersnatchRingRoot(create_dummy_bytes(144))
    slot_sealers = GammaSTickets(
        [TicketBody(create_dummy_bytes32(), i) for i in range(EPOCH_LENGTH)]
    )
    ticket_accumulator = GammaA(
        [TicketBody(create_dummy_bytes32(), i) for i in range(3)]
    )
    components["gamma"] = Gamma(
        k=validator_set,
        z=ring_root,
        s=GammaS(slot_sealers),
        a=ticket_accumulator,
    )

    # Delta - Service dictionary
    storage = AccountStorage(
        {create_dummy_bytes32(): Bytes(create_dummy_bytes(32)) for _ in range(3)}
    )
    lookup = PreImageLookup(
        {create_dummy_bytes32(): Bytes(create_dummy_bytes(64)) for _ in range(2)}
    )
    timestamps = LookupTimestamps(
        {
            create_dummy_bytes32(): Timestamps([U32(i) for i in range(3)])
            for _ in range(2)
        }
    )
    account = AccountData(
        storage=storage,
        lookup=lookup,
        timestamps=timestamps,
        code_hash=ServiceCodeHash(create_dummy_bytes32()),
        balance=Balance(1000),
        gas_limit=Gas(5000),
        min_gas=Gas(100),
    )
    components["delta"] = Delta({ServiceId(i): account for i in range(3)})

    # Simple components
    components["eta"] = Eta([OpaqueHash(create_dummy_bytes32()) for _ in range(4)])
    components["iota"] = Iota(dummy_validator_data)
    components["kappa"] = Kappa(dummy_validator_data)
    components["lambda_"] = Lambda_(dummy_validator_data)
    components["rho"] = Rho(
        [OptionalWorkReportState(Nullable()) for _ in range(CORE_COUNT)]
    )
    components["tau"] = Tau(0)

    # Phi - Authorization queue
    queue = AuthorizationQueue(
        [OpaqueHash(create_dummy_bytes32()) for _ in range(MAX_AUTH_QUEUE_ITEMS)]
    )
    components["phi"] = Phi([queue for _ in range(CORE_COUNT)])

    # Chi
    chi_g = ChiG({ServiceId(i): Gas(100) for i in range(3)})
    components["chi"] = Chi(m=ServiceId(0), a=ServiceId(1), v=ServiceId(2), g=chi_g)

    # Psi
    components["psi"] = Psi(
        PsiG([]),  # Empty array for good work reports
        PsiB([]),  # Empty array for bad work reports 
        PsiW([]),  # Empty array for wonky work reports
        PsiO([]),  # Empty array for offenders
    )
    # components["psi"] = Psi(
    #     PsiG([WorkReportHash(create_dummy_bytes32()) for _ in range(3)]),
    #     PsiB([WorkReportHash(create_dummy_bytes32()) for _ in range(3)]),
    #     PsiW([WorkReportHash(create_dummy_bytes32()) for _ in range(3)]),
    #     PsiO([Ed25519Public(create_dummy_bytes32()) for _ in range(3)]),
    # )

    # Pi
    all_validator_stats = AllValidatorStats(
        [
            ValidatorStat(
                blocks=Int(1),
                tickets=Int(1),
                pre_images=Int(1),
                pre_images_size=Int(1),
                guarantees=Int(1),
                assurances=Int(1),
            )
            for _ in range(VALIDATOR_COUNT)
        ]
    )
    components["pi"] = Pi([all_validator_stats for _ in range(2)])

    # Theta and Xi
    components["theta"] = Theta([AllReadyWRs([]) for _ in range(EPOCH_LENGTH)])
    components["xi"] = Xi(
        [WorkPackageHash(create_dummy_bytes32()) for _ in range(EPOCH_LENGTH)]
    )

    return components


def create_dummy_state() -> State:
    """Create a complete dummy state for testing"""
    return State(**create_dummy_state_components())
