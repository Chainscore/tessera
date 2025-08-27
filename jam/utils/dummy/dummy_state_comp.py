from typing import Dict

from jam.settings import Settings
from jam.types.protocol.ticket import TicketAttempt, TicketBody, TicketId
from jam.types.state.gamma import Gamma, GammaA, GammaK, GammaS, GammaSTickets
from jam.types.protocol.merkle import MMR
from jam.types.state.alpha import Alpha, AuthorizationPool, AuthorizerHash
from jam.types.state.beta import Beta, BlockHistory, BetaHistory, BeefyBelt
from jam.types.state.chi import Chi, ChiZ, ChiA
from jam.types.state.delta import (
    AccountData,
    AccountStorage,
    Delta,
    AccountLookup,
    AccountPreimages,
    ServiceCodeHash,
    Timestamps,
    AccountMetadata,
    Ao,
    Ai,
    LookupTable,
)
from jam.types import (
    Eta,
    Iota,
    Kappa,
    Lambda_,
    AuthorizationQueue,
    Phi,
    AllValidatorStats,
    Pi,
    ValidatorStat,
    AllCoreStats,
    CoreStat,
    AllServiceStats,
    Psi,
    PsiB,
    PsiG,
    PsiO,
    PsiW,
    OptionalWorkReportState,
    Rho,
    Tau,
    AllReadyWRs,
    Omega,
    Xi,
    BeefyRoot,
)

from jam.state.state import State
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, U32, U8, Uint
from tsrkit_types.null import Null

from jam.types.protocol.crypto import (
    BlsPublic,
    Ed25519Public,
    HeaderHash,
    OpaqueHash,
    StateRoot,
    BandersnatchPublic,
    BandersnatchRingRoot,
)
from jam.types.work import SegmentRootLookup
from jam.types.protocol.core import (
    SegmentRoot,
    WorkPackageHash,
    Balance,
    Gas,
    ServiceId,
)
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata, IPAddress
from jam.types.work import WorkDependencies
from jam.utils.constants import (
    CORE_COUNT,
    EPOCH_LENGTH,
    MAX_AUTH_POOL_ITEMS,
    MAX_AUTH_QUEUE_ITEMS,
    VALIDATOR_COUNT,
)
from jam.utils.dummy.utils import create_dummy_bytes, create_dummy_bytes32


def create_dummy_state_components() -> Dict[str, object]:
    """Create dummy instances of all state components with realistic test data"""
    components: Dict[str, object] = {}

    # Alpha - Array of authorization pools
    auth_pool = AuthorizationPool(
        [AuthorizerHash(create_dummy_bytes32()) for _ in range(MAX_AUTH_POOL_ITEMS)]
    )
    components["alpha"] = Alpha([auth_pool for _ in range(CORE_COUNT)])

    # Beta - Vector of block history
    package_dict = SegmentRootLookup(
        {
            WorkPackageHash(create_dummy_bytes32()): SegmentRoot(create_dummy_bytes32())
            for _ in range(3)  # Few dummy packages
        }
    )
    block = BlockHistory(
        header_hash=HeaderHash(create_dummy_bytes32()),
        state_root=StateRoot(create_dummy_bytes32()),
        beefy_root=BeefyRoot(create_dummy_bytes32()),
        reported=package_dict,
    )
    components["beta"] = Beta(h=BetaHistory([block for _ in range(3)]), b=BeefyBelt([]))

    # Create dummy validator data
    key_set = [Settings(data_path=None, seed=i) for i in range(VALIDATOR_COUNT)]
    dummy_validator_data = [
        ValidatorData(
            bandersnatch=BandersnatchPublic(key.bandersnatch_public),
            ed25519=Ed25519Public(key.ed25519_public),
            bls=BlsPublic(create_dummy_bytes(144)),
            metadata=ValidatorMetadata.from_json(bytes(128).hex()),
        )
        for key in key_set
    ]

    # Gamma - Validator set
    validator_set = GammaK(dummy_validator_data)
    ring_root = BandersnatchRingRoot(create_dummy_bytes(144))
    slot_sealers = GammaSTickets(
        [
            TicketBody(TicketId(create_dummy_bytes32()), TicketAttempt(i))
            for i in range(EPOCH_LENGTH)
        ]
    )
    ticket_accumulator = GammaA(
        [TicketBody(TicketId(create_dummy_bytes32()), TicketAttempt(i)) for i in range(3)]
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
    lookup = AccountPreimages(
        {create_dummy_bytes32(): Bytes(create_dummy_bytes(64)) for _ in range(2)}
    )
    timestamps = AccountLookup(
        {
            LookupTable(hash=Bytes[32](create_dummy_bytes32()), length=Uint[32](0)): Timestamps(
                [U32(i) for i in range(3)]
            )
            for _ in range(2)
        }
    )
    account = AccountData(
        storage=storage,
        preimages=lookup,
        lookup=timestamps,
        service=AccountMetadata(
            code_hash=ServiceCodeHash(create_dummy_bytes32()),
            balance=Balance(1000),
            gas_limit=Gas(5000),
            min_gas=Gas(100),
            num_o=Ao(0),
            num_i=Ai(0),
        ),
    )
    components["delta"] = Delta({ServiceId(i): account for i in range(3)})

    # Simple components
    components["eta"] = Eta([OpaqueHash(create_dummy_bytes32()) for _ in range(4)])
    components["iota"] = Iota(dummy_validator_data)
    components["kappa"] = Kappa(dummy_validator_data)
    components["lambda_"] = Lambda_(dummy_validator_data)
    components["rho"] = Rho([OptionalWorkReportState(Null) for _ in range(CORE_COUNT)])
    components["tau"] = Tau(0)

    # Phi - Authorization queue
    queue = AuthorizationQueue(
        [OpaqueHash(create_dummy_bytes32()) for _ in range(MAX_AUTH_QUEUE_ITEMS)]
    )
    components["phi"] = Phi([queue for _ in range(CORE_COUNT)])

    # Chi
    chi_z = ChiZ({ServiceId(i): Gas(100) for i in range(3)})
    chi_a = ChiA([ServiceId(i) for i in range(CORE_COUNT)])
    components["chi"] = Chi(
        chi_m=ServiceId(0), chi_a=chi_a, chi_v=ServiceId(2), chi_g=chi_z
    )

    # Psi
    components["psi"] = Psi(
        PsiG([]),  # Empty array for good work reports
        PsiB([]),  # Empty array for bad work reports
        PsiW([]),  # Empty array for wonky work reports
        PsiO([]),  # Empty array for offenders
    )

    # Pi
    components["pi"] = Pi(
        vals_current=AllValidatorStats.empty(),
        vals_last=AllValidatorStats.empty(),
        cores=AllCoreStats.empty(),
        services=AllServiceStats({}),
    )

    # Omega (ω) and Xi (ξ)
    components["omega"] = Omega([AllReadyWRs([]) for _ in range(EPOCH_LENGTH)])
    components["xi"] = Xi([WorkDependencies([]) for _ in range(EPOCH_LENGTH)])

    return components


def create_dummy_state() -> State:
    """Create a complete dummy state for testing"""
    return State(**create_dummy_state_components())
