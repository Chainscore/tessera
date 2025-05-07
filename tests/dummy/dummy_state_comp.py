from typing import Dict

from jam.consensus.safrole.gamma import Gamma, GammaA, GammaK, GammaS, GammaSTickets
from jam.types.protocol.merkle import MMR
from jam.types.state.alpha import Alpha, AuthorizationPool, AuthorizerHash
from jam.types.state.beta import Beta, BlockHistory, PackageDict
from jam.types.state.chi import Chi, ChiG
from jam.types.state.delta import (
    AccountData,
    AccountStorage,
    Delta,
    LookupTimestamps,
    PreImageLookup,
    ServiceCodeHash,
    Timestamps,
)
from jam.types.state.eta import Eta
from jam.types.state.iota import Iota
from jam.types.state.kappa import Kappa
from jam.types.state.lambda_ import Lambda_
from jam.types.state.phi import AuthorizationQueue, Phi
from jam.types.state.pi import AllValidatorStats, Pi, ValidatorStat, AllCoreStats, CoreStat, AllServiceStats
from jam.types.state.psi import Psi, PsiB, PsiG, PsiO, PsiW
from jam.types.state.rho import OptionalWorkReportState, Rho
from jam.types.state.tau import Tau
from jam.types.state.nu import AllReadyWRs, Nu
from jam.types.state.xi import Xi

from jam.types import TicketBody, Array, Vector

from jam.state.state import State
from jam.types.base import Bytes
from jam.types.base.integers.fixed import U16, U32, U8
from jam.types.base.integers.general import Int
from jam.types.base.null import Nullable

from jam.types.protocol.crypto import (
    BandersnatchPublic,
    BandersnatchRingRoot,
    BlsPublic,
    Ed25519Public,
    HeaderHash,
    OpaqueHash,
    StateRoot,
    BandersnatchPublic,
    BandersnatchRingRoot,
)
from jam.types.work.report import WorkDependencies
from jam.types.protocol.core import (
    SegmentRoot,
    WorkPackageHash,
    Balance,
    Gas,
    ServiceId,
    WorkReportHash,
)
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata, ValidatorName, IPAddress
from jam.types.work.report import WorkDependencies
from jam.utils.constants import (
    CORE_COUNT,
    EPOCH_LENGTH,
    MAX_AUTH_POOL_ITEMS,
    MAX_AUTH_QUEUE_ITEMS,
    VALIDATOR_COUNT,
)
from tests.dummy.utils import create_dummy_bytes, create_dummy_bytes32


def create_dummy_state_components() -> Dict[str, object]:
    """Create dummy instances of all state components with realistic test data"""
    components: Dict[str, object] = {}

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
            metadata=ValidatorMetadata(name=ValidatorName(""), host=IPAddress([U8(127), U8(0), U8(0), U8(1)]), port=U16(0)),
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
    components["chi"] = Chi(chi_m=ServiceId(0), chi_a=ServiceId(1), chi_v=ServiceId(2), chi_g=chi_g)

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
    all_core_stats = AllCoreStats(
        [
            CoreStat(
                gas_used=Int(1),
                imports=Int(1),
                extrinsic_count=Int(1),
                extrinsic_size=Int(1),
                exports=Int(1),
                bundle_size=Int(1),
                da_load=Int(1),
                popularity=Int(1),
            )
            for _ in range(CORE_COUNT)
        ]
    )
    all_service_stats = AllServiceStats()

    components["pi"] = Pi(
        vals_current=all_validator_stats,
        vals_last=all_validator_stats,
        cores=all_core_stats,
        services=all_service_stats
    )

    # Nu and Xi
    components["nu"] = Nu([AllReadyWRs([]) for _ in range(EPOCH_LENGTH)])


    components["xi"] = Xi(
        [WorkDependencies([]) for _ in range(EPOCH_LENGTH)]
    )

    return components


def create_dummy_state() -> State:
    """Create a complete dummy state for testing"""
    return State(**create_dummy_state_components())
